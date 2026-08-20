#!/usr/bin/env python3
"""rageval/optimize.py — Loop A: tối ưu config RAG bằng oracle eval + ledger chống lặp.

Oracle = runner.py trên subset cố định (~30 câu, mode hybrid) với composite =
mean(faithfulness, answer_relevance, context_precision). Mỗi vòng đổi ĐÚNG 1 knob:
  - env (reload nóng): NEXUSRAG_RERANKER_TOP_K, NEXUSRAG_VECTOR_PREFETCH, ...
    (sửa backend/.env + touch app/main.py → uvicorn --reload tự nạp)
  - prompt (API):      SYSTEM_PROMPT_WS<id>=<text|@file> (PUT /workspaces/{id})
Giữ nếu composite tăng so với best; ngược lại tự ROLLBACK. Ledger:
cache/experiments.jsonl (config_hash chống thử lại trùng).

Lệnh:
  python3 optimize.py make-subset [--n 30]
  python3 optimize.py baseline
  python3 optimize.py apply-and-run --set KEY=VAL [--hypothesis "..."]
  python3 optimize.py status          # bảng lịch sử + stop-rule (3 vòng ≤1% | 30 vòng)
  python3 optimize.py restore --original|--best
"""
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time

from common import (HERE, PROJECT_ROOT, http_json, log, read_jsonl, append_jsonl,
                    sha1, now_ts)

BACKEND_APP = os.path.join(PROJECT_ROOT, "micco-backend", "backend")
ENV_FILE = os.path.join(BACKEND_APP, ".env")
ENV_BACKUP = os.path.join(BACKEND_APP, ".env.rageval-backup")
TOUCH_FILE = os.path.join(BACKEND_APP, "app", "main.py")
LEDGER = os.path.join(HERE, "cache", "experiments.jsonl")
SUBSET = os.path.join(HERE, "datasets", "optimize_subset.jsonl")

ENV_KNOBS = {  # knob → (default khi không có trong .env, min, max)
    "NEXUSRAG_RERANKER_TOP_K": (8, 3, 15),
    "NEXUSRAG_VECTOR_PREFETCH": (20, 8, 50),
    "NEXUSRAG_RERANKER_MIN_SCORE": (0.15, 0.0, 0.9),
    "NEXUSRAG_CHUNK_MAX_TOKENS": (512, 256, 1024),      # ĐẮT: cần re-ingest ws bench
    "NEXUSRAG_KG_CHUNK_TOKEN_SIZE": (800, 400, 1600),   # ĐẮT: cần re-ingest ws bench
}
random.seed(20260723)


# ---------------------------------------------------------------------------
# .env thao tác an toàn (chỉ dòng NEXUSRAG_*, có backup)
# ---------------------------------------------------------------------------

def read_env():
    vals = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^([A-Z0-9_]+)\s*=\s*(.*)$", line.strip())
                if m:
                    vals[m.group(1)] = m.group(2)
    return vals


def ensure_backup():
    if not os.path.exists(ENV_BACKUP):
        shutil.copy2(ENV_FILE, ENV_BACKUP)
        log("  🔒 backup .env → %s" % os.path.basename(ENV_BACKUP))


def set_env_var(key, value):
    """Chỉ cho phép key NEXUSRAG_*. Sửa/thêm dòng, giữ nguyên phần còn lại."""
    assert key.startswith("NEXUSRAG_"), "chỉ được sửa NEXUSRAG_*"
    ensure_backup()
    with open(ENV_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    pat = re.compile(r"^%s\s*=" % re.escape(key))
    done = False
    for i, line in enumerate(lines):
        if pat.match(line.strip()):
            lines[i] = "%s=%s\n" % (key, value)
            done = True
            break
    if not done:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append("# rageval optimize\n%s=%s\n" % (key, value))
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)


def unset_env_var(key):
    """Xóa dòng key (trả về default trong config.py)."""
    assert key.startswith("NEXUSRAG_")
    with open(ENV_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    pat = re.compile(r"^%s\s*=" % re.escape(key))
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(l for l in lines if not pat.match(l.strip()))


def reload_backend(timeout=90):
    """touch app/main.py → uvicorn --reload tự khởi động lại → chờ /health."""
    os.utime(TOUCH_FILE, None)
    time.sleep(4)
    deadline = time.time() + timeout
    while time.time() < deadline:
        st, body = http_json("GET", "/health", timeout=8)
        if st == 200:
            time.sleep(6)  # chờ ổn định
            st2, _ = http_json("GET", "/health", timeout=8)
            if st2 == 200:
                return True
        time.sleep(3)
    return False


def set_system_prompt(ws_id, text):
    st, body = http_json("PUT", "/api/v1/workspaces/%d" % ws_id,
                         {"system_prompt": text}, timeout=30)
    return st == 200


def get_system_prompt(ws_id):
    st, body = http_json("GET", "/api/v1/workspaces/%d" % ws_id, timeout=30)
    return (body or {}).get("system_prompt") if st == 200 else None


# ---------------------------------------------------------------------------
# Config hiện tại + hash
# ---------------------------------------------------------------------------

def current_config():
    env = read_env()
    cfg = {}
    for k, (default, _, _) in ENV_KNOBS.items():
        cfg[k] = env.get(k, str(default))
    subset_ws = sorted({it["workspace_id"] for it in read_jsonl(SUBSET)})
    for ws in subset_ws:
        sp = get_system_prompt(ws)
        cfg["SYSTEM_PROMPT_WS%d" % ws] = sha1(sp or "")[:12]
    return cfg


# ---------------------------------------------------------------------------
# Oracle
# ---------------------------------------------------------------------------

def run_oracle(tag):
    run_dir = os.path.join(HERE, "cache", "opt-%s" % tag)
    score_json = os.path.join(run_dir, "score.json")
    env = dict(os.environ)
    env.update({
        "RAGEVAL_SUBSET": SUBSET, "RAGEVAL_MODES": "hybrid",
        "RAGEVAL_RUN_DIR": run_dir, "RAGEVAL_JSON": score_json,
        "RAGEVAL_MD": os.path.join(run_dir, "score.md"),
        "RAGEVAL_MIN_CORRECT": "0", "RAGEVAL_MIN_FAITHFUL": "0",
    })
    rc = subprocess.call([sys.executable, os.path.join(HERE, "runner.py")], env=env)
    if not os.path.exists(score_json):
        raise RuntimeError("oracle không tạo được score.json (rc=%s)" % rc)
    with open(score_json, encoding="utf-8") as f:
        result = json.load(f)
    g = result["aggregate"].get("ALL|hybrid|ALL", {})
    scores = {"faithfulness": g.get("faithfulness"),
              "answer_relevance": g.get("answer_relevance"),
              "context_precision": g.get("context_precision")}
    vals = [v for v in scores.values() if v is not None]
    scores["composite"] = round(sum(vals) / len(vals), 4) if vals else 0.0

    def composite(r):
        vs = [v for v in (r.get("faithfulness"), r.get("answer_relevance"),
                          r.get("context_precision")) if v is not None]
        return sum(vs) / len(vs) if vs else None

    worst = sorted([(composite(r), r) for r in result["items"]
                    if not r.get("error") and composite(r) is not None])[:5]
    top_fail = [{"id": r["id"], "composite": round(s, 3),
                 "faithful": r.get("faithfulness"),
                 "ans_rel": r.get("answer_relevance"),
                 "ctx_prec": r.get("context_precision")} for s, r in worst]
    return scores, top_fail


def best_composite():
    rows = [r for r in read_jsonl(LEDGER) if r.get("verdict") in ("keep", "baseline")]
    return max((r["scores"]["composite"] for r in rows), default=None)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_make_subset(n):
    items = []
    for name in ("golden_self.jsonl", "golden_hf.jsonl"):
        items.extend(read_jsonl(os.path.join(HERE, "datasets", name)))
    if not items:
        log("❌ chưa có dataset nào")
        return 2
    by_type = {}
    for it in items:
        by_type.setdefault(it.get("question_type", "single"), []).append(it)
    out = []
    quota = {"single": 0.35, "multi": 0.45, "unanswerable": 0.2}
    for t, frac in quota.items():
        cand = by_type.get(t, [])
        random.shuffle(cand)
        out.extend(cand[:max(1, int(n * frac))])
    out = out[:n]
    if os.path.exists(SUBSET):
        os.remove(SUBSET)
    for it in out:
        append_jsonl(SUBSET, it)
    dist = {}
    for it in out:
        dist[it["question_type"]] = dist.get(it["question_type"], 0) + 1
    log("  ✅ subset %d item %s → %s" % (len(out), dist, SUBSET))
    return 0


def cmd_baseline():
    if not os.path.exists(SUBSET):
        log("❌ chưa có subset — chạy make-subset trước")
        return 2
    cfg = current_config()
    scores, top_fail = run_oracle("baseline-%s" % now_ts())
    append_jsonl(LEDGER, {"iter": 0, "ts": now_ts(), "knob": None,
                          "old": None, "new": None, "hypothesis": "baseline",
                          "config": cfg, "config_hash": sha1(json.dumps(cfg, sort_keys=True)),
                          "scores": scores, "delta_vs_best": 0.0,
                          "verdict": "baseline", "top_fail": top_fail})
    log("  ✅ baseline composite=%.4f %s" % (scores["composite"], scores))
    return 0


def cmd_apply_and_run(setting, hypothesis):
    key, _, value = setting.partition("=")
    key = key.strip()
    rows = read_jsonl(LEDGER)
    if not rows:
        log("❌ chưa có baseline")
        return 2
    it_no = max(r["iter"] for r in rows) + 1
    best = best_composite() or 0.0

    # chuẩn bị apply + nhớ giá trị cũ để rollback
    is_prompt = key.startswith("SYSTEM_PROMPT_WS")
    if is_prompt:
        ws_id = int(key.replace("SYSTEM_PROMPT_WS", ""))
        if value.startswith("@"):
            with open(value[1:], encoding="utf-8") as f:
                value = f.read()
        old = get_system_prompt(ws_id) or ""
        apply_fn = lambda v: set_system_prompt(ws_id, v)
        rollback_fn = lambda: set_system_prompt(ws_id, old)
        old_repr = sha1(old)[:12]
        new_repr = sha1(value)[:12]
    else:
        if key not in ENV_KNOBS:
            log("❌ knob không hợp lệ: %s (cho phép: %s + SYSTEM_PROMPT_WS<id>)"
                % (key, ",".join(ENV_KNOBS)))
            return 2
        default, lo, hi = ENV_KNOBS[key]
        try:
            fv = float(value)
            assert lo <= fv <= hi
        except (ValueError, AssertionError):
            log("❌ giá trị %s ngoài khoảng [%s..%s]" % (value, lo, hi))
            return 2
        env = read_env()
        old = env.get(key)  # None = chưa có (dùng default)
        apply_fn = lambda v: (set_env_var(key, v), reload_backend())
        rollback_fn = lambda: ((set_env_var(key, old) if old is not None
                                else unset_env_var(key)), reload_backend())
        old_repr = old if old is not None else "(default %s)" % default
        new_repr = value

    # chống thử trùng
    cfg_after = current_config()
    cfg_after[key if not is_prompt else key] = new_repr
    h = sha1(json.dumps(cfg_after, sort_keys=True))
    if any(r.get("config_hash") == h for r in rows):
        log("⚠️  config này đã thử rồi (hash trùng trong ledger) — bỏ qua")
        return 3

    log("▶ iter %d: %s: %s → %s | best=%.4f" % (it_no, key, old_repr, new_repr, best))
    applied = False
    try:
        apply_fn(value)
        applied = True
        st, _ = http_json("GET", "/health", timeout=10)
        if st != 200:
            raise RuntimeError("backend không healthy sau apply")
        scores, top_fail = run_oracle("it%02d-%s" % (it_no, now_ts()))
        delta = scores["composite"] - best
        verdict = "keep" if delta > 1e-9 else "rollback"
        if verdict == "rollback":
            rollback_fn()
        append_jsonl(LEDGER, {"iter": it_no, "ts": now_ts(), "knob": key,
                              "old": old_repr, "new": new_repr,
                              "hypothesis": hypothesis or "",
                              "config": cfg_after, "config_hash": h,
                              "scores": scores,
                              "delta_vs_best": round(delta, 4),
                              "verdict": verdict, "top_fail": top_fail})
        log("  %s iter %d: composite=%.4f (Δ%+.4f) → %s" % (
            "✅" if verdict == "keep" else "↩️", it_no,
            scores["composite"], delta, verdict.upper()))
        return 0 if verdict == "keep" else 1
    except Exception as e:
        log("❌ iter %d lỗi: %s — rollback" % (it_no, e))
        if applied:
            try:
                rollback_fn()
            except Exception as e2:
                log("‼️  rollback cũng lỗi: %s — kiểm tra %s và %s bằng tay!"
                    % (e2, ENV_FILE, ENV_BACKUP))
        append_jsonl(LEDGER, {"iter": it_no, "ts": now_ts(), "knob": key,
                              "old": old_repr, "new": new_repr,
                              "hypothesis": hypothesis or "", "config_hash": h,
                              "scores": {"composite": None}, "verdict": "error",
                              "error": str(e)[:300]})
        return 2


def cmd_status():
    rows = read_jsonl(LEDGER)
    if not rows:
        log("(ledger rỗng)")
        return 0
    best = best_composite() or 0.0
    log("%-4s %-28s %-14s %-9s %-8s %s" % ("it", "knob", "old→new", "composite",
                                           "Δbest", "verdict"))
    for r in rows:
        log("%-4s %-28s %-14s %-9s %-8s %s" % (
            r["iter"], r.get("knob") or "-",
            ("%s→%s" % (r.get("old"), r.get("new")))[:14],
            r["scores"].get("composite"),
            r.get("delta_vs_best", ""), r["verdict"]))
    log("best composite = %.4f" % best)
    # stop rule
    real = [r for r in rows if r["verdict"] in ("keep", "rollback")]
    stop = None
    if len(real) >= 30:
        stop = "đã đủ 30 vòng"
    elif len(real) >= 3:
        last3 = real[-3:]
        if all((r["scores"].get("composite") or 0) <= best * 1.01 and
               r["verdict"] == "rollback" for r in last3):
            stop = "3 vòng liên tiếp không cải thiện >1%"
    log("STOP-RULE: %s" % (stop or "chưa chạm — tiếp tục"))
    return 0


def cmd_restore(which):
    if which == "original":
        if not os.path.exists(ENV_BACKUP):
            log("(chưa từng backup — .env nguyên bản)")
            return 0
        shutil.copy2(ENV_BACKUP, ENV_FILE)
        ok = reload_backend()
        log("  ✅ khôi phục .env gốc, backend %s" % ("healthy" if ok else "LỖI"))
        return 0 if ok else 2
    # --best: áp lại mọi knob env của config best từ ledger
    rows = [r for r in read_jsonl(LEDGER) if r["verdict"] in ("keep", "baseline")]
    if not rows:
        log("❌ ledger không có config keep nào")
        return 2
    bestrow = max(rows, key=lambda r: r["scores"]["composite"])
    log("  áp config best (iter %d, composite %.4f)" % (
        bestrow["iter"], bestrow["scores"]["composite"]))
    for k, v in (bestrow.get("config") or {}).items():
        if k in ENV_KNOBS:
            set_env_var(k, v)
    ok = reload_backend()
    log("  ✅ done, backend %s" % ("healthy" if ok else "LỖI"))
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("make-subset")
    s.add_argument("--n", type=int, default=30)
    sub.add_parser("baseline")
    s = sub.add_parser("apply-and-run")
    s.add_argument("--set", dest="setting", required=True, metavar="KEY=VAL")
    s.add_argument("--hypothesis", default="")
    sub.add_parser("status")
    s = sub.add_parser("restore")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--original", action="store_true")
    g.add_argument("--best", action="store_true")
    args = ap.parse_args()
    if args.cmd == "make-subset":
        return cmd_make_subset(args.n)
    if args.cmd == "baseline":
        return cmd_baseline()
    if args.cmd == "apply-and-run":
        return cmd_apply_and_run(args.setting, args.hypothesis)
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "restore":
        return cmd_restore("original" if args.original else "best")


if __name__ == "__main__":
    sys.exit(main())
