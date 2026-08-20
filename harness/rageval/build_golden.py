#!/usr/bin/env python3
"""rageval/build_golden.py — Loop B: xây bộ golden tự build từ corpus thật, có vòng làm sạch.

Vòng lặp mỗi mẻ (batch):
  sinh N cặp Q/A (single/multi/unanswerable từ chunks + KG thật)
  → verifier ĐỘC LẬP chấm pass/fail ("đáp án có suy ra được CHỈ từ chunk trích dẫn?")
  → loại fail, gom lý do → tự chỉnh generation prompt (counter-instruction)
  → mẻ tiếp. DỪNG: pass ≥ TARGET (0.95) 2 mẻ liên tiếp, hoặc hết MAX_BATCHES.

Lệnh:
  python3 build_golden.py --workspaces 1,3,4 --loop [--batch-size 200] [--max-batches 5]
  python3 build_golden.py --review                  # dedupe + cân bằng + xuất sheet duyệt
  python3 build_golden.py --finalize <review.csv>   # áp quyết định user → golden_self.jsonl
"""
import argparse
import csv
import json
import os
import random
import sys
import time

from common import (HERE, gemini_embed, cosine, http_json, log, pmap,
                    read_jsonl, append_jsonl, sha1)
import judge as J

DS_DIR = os.path.join(HERE, "datasets")
REVIEW_DIR = os.path.join(DS_DIR, "review")
POOL = os.path.join(REVIEW_DIR, "golden_pool.jsonl")
HISTORY = os.path.join(REVIEW_DIR, "genloop_history.jsonl")
FINAL = os.path.join(DS_DIR, "golden_self.jsonl")

GEN_DATE = time.strftime("%Y-%m-%d")
random.seed(20260723)

# ---------------------------------------------------------------------------
# Prompt sinh + counter-instructions
# ---------------------------------------------------------------------------

BASE_RULES = """QUY TẮC BẮT BUỘC:
- Câu hỏi phải trả lời được CHỈ từ đoạn văn cung cấp, không cần kiến thức ngoài.
- Đáp án ngắn gọn 1-3 câu, chính xác tuyệt đối về số liệu/tên riêng theo đoạn văn.
- Câu hỏi tự nhiên như người dùng thật hỏi chatbot nội bộ, KHÔNG tham chiếu "đoạn văn này"/"tài liệu trên".
- Tiếng Việt chuẩn."""

COUNTER_INSTRUCTIONS = {
    "ngoai_kien_thuc": "- KHÔNG tạo đáp án chứa bất kỳ thông tin nào không có mặt trong đoạn văn (kể cả kiến thức phổ thông đúng).",
    "sai_so_lieu": "- Kiểm tra lại TỪNG con số/tên riêng trong đáp án phải khớp nguyên văn đoạn văn.",
    "mo_ho": "- Câu hỏi phải có MỘT đáp án xác định duy nhất từ đoạn văn; tránh câu hỏi mở/ý kiến.",
    "khong_suy_ra": "- Đáp án phải suy ra trực tiếp từ đoạn văn; nếu đoạn văn không đủ ý thì bỏ, tạo câu khác.",
    "single_hop_gia": "- Với câu multi-hop: câu hỏi phải BẮT BUỘC dùng thông tin của CẢ HAI đoạn; nếu một đoạn đủ trả lời thì làm lại.",
    "khac": "- Tự soát lại chất lượng: câu hỏi rõ ràng, đáp án đúng và đủ.",
}

VERIFIER_SYSTEM = ("Bạn là người kiểm định chất lượng dữ liệu đánh giá, độc lập với người tạo. "
                   "Khắt khe: nghi ngờ thì đánh fail. Chỉ trả về JSON.")


def gen_prompt_single(chunk_text, extra):
    return f"""Tạo MỘT cặp câu hỏi - đáp án chuẩn từ đoạn văn sau (dùng cho bộ đánh giá chatbot hỏi-đáp tài liệu nội bộ).

{BASE_RULES}
{extra}

ĐOẠN VĂN:
{chunk_text[:6000]}

Trả về JSON: {{"question": "...", "answer": "...", "keywords": ["1-3 từ khóa nhận diện"], "difficulty": "easy|medium|hard"}}"""


def gen_prompt_multi(chunk_a, chunk_b, relation, extra):
    return f"""Tạo MỘT câu hỏi MULTI-HOP: bắt buộc phải KẾT HỢP thông tin từ CẢ HAI đoạn văn dưới đây mới trả lời được
(so sánh / nhân quả / tổng hợp / nối chuỗi thực thể). Nếu một đoạn đủ trả lời thì KHÔNG đạt.

{BASE_RULES}
{extra}

GỢI Ý LIÊN KẾT: {relation}

ĐOẠN A:
{chunk_a[:4500]}

ĐOẠN B:
{chunk_b[:4500]}

Trả về JSON: {{"question": "...", "answer": "...", "keywords": ["1-3 từ khóa"], "difficulty": "medium|hard"}}"""


def gen_prompt_unanswerable(titles_headings, extra):
    return f"""Kho tài liệu nội bộ có các tài liệu/mục sau:
{titles_headings[:4000]}

Tạo MỘT câu hỏi CÙNG CHỦ ĐỀ với kho tài liệu nhưng hỏi về CHI TIẾT KHÔNG CÓ trong đó
(ví dụ: số liệu của năm khác, chính sách chưa đề cập, con người/phòng ban không nêu, phiên bản tương lai).
Câu hỏi phải nghe hợp lý như người dùng thật; KHÔNG hỏi kiến thức phổ thông ngoài phạm vi chủ đề kho.
{extra}

Trả về JSON: {{"question": "...", "topic_hint": "chủ đề liên quan"}}"""


def verify_prompt(item):
    passages = "\n\n---\n\n".join(p[:4500] for p in item["gold_passages"])
    multi_extra = ""
    if item["question_type"] == "multi":
        multi_extra = ('\n4. "single_hop_gia": chỉ cần MỘT trong các đoạn đã đủ trả lời '
                       '(không thật sự multi-hop) → fail.')
    return f"""Kiểm định cặp câu hỏi - đáp án dưới đây cho bộ đánh giá chatbot.

TIÊU CHÍ FAIL (nghi ngờ thì fail):
1. "khong_suy_ra": đáp án KHÔNG suy ra được chỉ từ (các) đoạn trích dẫn.
2. "ngoai_kien_thuc": đáp án chứa thông tin ngoài đoạn trích dẫn.
3. "sai_so_lieu": số liệu/tên riêng trong đáp án khác với đoạn trích dẫn.
5. "mo_ho": câu hỏi mơ hồ, nhiều cách hiểu, hoặc không có đáp án xác định.{multi_extra}

(CÁC) ĐOẠN TRÍCH DẪN:
{passages}

CÂU HỎI: {item["question"]}
ĐÁP ÁN: {item["golden_answer"]}

Trả về JSON: {{"verdict": "pass|fail", "reason": "khong_suy_ra|ngoai_kien_thuc|sai_so_lieu|mo_ho|single_hop_gia|khac|ok", "note": "<1 câu>"}}"""


# ---------------------------------------------------------------------------
# Inventory: chunks + KG từ backend
# ---------------------------------------------------------------------------

def load_inventory(workspaces):
    inv = {"chunks": [], "docs": {}, "relations": {}, "titles": {}}
    for ws in workspaces:
        st, docs = http_json("GET", "/api/v1/documents/workspace/%d" % ws, timeout=30)
        if st != 200 or not isinstance(docs, list):
            log("  ⚠️  ws%d: không lấy được docs (%s)" % (ws, st))
            continue
        titles = []
        for d in docs:
            if d.get("status") != "indexed":
                continue
            doc_id = d["id"]
            inv["docs"][doc_id] = {"ws": ws, "filename": d.get("original_filename", "")}
            titles.append(d.get("original_filename", ""))
            st2, ch = http_json("GET", "/api/v1/rag/chunks/%d" % doc_id, timeout=60)
            if st2 == 200 and isinstance(ch, dict):
                for c in ch.get("chunks", []):
                    content = c.get("content") or ""
                    if len(content) >= 200:
                        inv["chunks"].append({
                            "ws": ws, "doc_id": doc_id,
                            "chunk_id": c["chunk_id"], "content": content,
                            "heading": (c.get("metadata") or {}).get("heading_path", "")})
        inv["titles"][ws] = titles
        st3, rels = http_json("GET", "/api/v1/rag/relationships/%d" % ws, timeout=60)
        inv["relations"][ws] = rels if (st3 == 200 and isinstance(rels, list)) else []
        log("  ws%d: %d chunks, %d relations, %d docs indexed" % (
            ws, sum(1 for c in inv["chunks"] if c["ws"] == ws),
            len(inv["relations"][ws]), len(titles)))
    return inv


def find_multihop_pairs(inv, max_pairs=200):
    """Cặp chunk ở 2 doc khác nhau nối qua 1 relation KG (match tên entity trong content)."""
    pairs = []
    seen = set()
    for ws, rels in inv["relations"].items():
        ws_chunks = [c for c in inv["chunks"] if c["ws"] == ws]
        for r in rels:
            src = (r.get("source") or "").strip().lower()
            tgt = (r.get("target") or "").strip().lower()
            if len(src) < 3 or len(tgt) < 3:
                continue
            ca = [c for c in ws_chunks if src in c["content"].lower()]
            cb = [c for c in ws_chunks if tgt in c["content"].lower()]
            random.shuffle(ca)
            random.shuffle(cb)
            for a in ca[:3]:
                for b in cb[:3]:
                    if a["doc_id"] == b["doc_id"]:
                        continue
                    key = (min(a["chunk_id"], b["chunk_id"]), max(a["chunk_id"], b["chunk_id"]))
                    if key in seen:
                        continue
                    seen.add(key)
                    pairs.append({"a": a, "b": b,
                                  "relation": "%s → %s: %s" % (
                                      r.get("source"), r.get("target"),
                                      (r.get("description") or "")[:200])})
                    break
                else:
                    continue
                break
    random.shuffle(pairs)
    # fallback: cặp chunk cùng doc khác heading (khi KG thưa)
    if len(pairs) < max_pairs // 2:
        by_doc = {}
        for c in inv["chunks"]:
            by_doc.setdefault(c["doc_id"], []).append(c)
        for doc_id, cs in by_doc.items():
            heads = {}
            for c in cs:
                heads.setdefault(c["heading"][:40], c)
            hs = list(heads.values())
            for i in range(0, len(hs) - 1, 2):
                pairs.append({"a": hs[i], "b": hs[i + 1],
                              "relation": "hai mục khác nhau trong cùng tài liệu"})
    return pairs[:max_pairs]


# ---------------------------------------------------------------------------
# Sinh 1 mẻ
# ---------------------------------------------------------------------------

def gen_batch(inv, batch_no, batch_size, extra_rules, id_seq):
    n_single = int(batch_size * 0.5)
    n_multi = int(batch_size * 0.3)
    n_unans = batch_size - n_single - n_multi
    extra = "\n".join(extra_rules)
    tasks = []

    chunks = [c for c in inv["chunks"]]
    random.shuffle(chunks)
    for c in chunks[:n_single]:
        tasks.append(("single", c))
    pairs = find_multihop_pairs(inv, max_pairs=n_multi * 2)
    for p in pairs[:n_multi]:
        tasks.append(("multi", p))
    all_titles = []
    for ws, ts in inv["titles"].items():
        heads = sorted({c["heading"] for c in inv["chunks"] if c["ws"] == ws and c["heading"]})
        all_titles.append((ws, "WS%d:\n" % ws + "\n".join("- " + t for t in ts)
                           + "\nMục: " + "; ".join(heads[:40])))
    for i in range(n_unans):
        tasks.append(("unanswerable", all_titles[i % len(all_titles)]))

    def gen_one(task):
        kind, payload = task
        from common import gemini_generate
        if kind == "single":
            out = gemini_generate(gen_prompt_single(payload["content"], extra),
                                  max_tokens=1024)
            return {"question_type": "single", "workspace_id": payload["ws"],
                    "question": out.get("question", ""), "golden_answer": out.get("answer", ""),
                    "gold_doc_ids": [payload["doc_id"]],
                    "gold_chunk_ids": [payload["chunk_id"]],
                    "gold_passages": [payload["content"]],
                    "expected_keywords": out.get("keywords", [])[:3],
                    "difficulty": out.get("difficulty", "medium")}
        if kind == "multi":
            a, b = payload["a"], payload["b"]
            out = gemini_generate(gen_prompt_multi(a["content"], b["content"],
                                                   payload["relation"], extra),
                                  max_tokens=1024)
            return {"question_type": "multi", "workspace_id": a["ws"],
                    "question": out.get("question", ""), "golden_answer": out.get("answer", ""),
                    "gold_doc_ids": sorted({a["doc_id"], b["doc_id"]}),
                    "gold_chunk_ids": [a["chunk_id"], b["chunk_id"]],
                    "gold_passages": [a["content"], b["content"]],
                    "expected_keywords": out.get("keywords", [])[:3],
                    "difficulty": out.get("difficulty", "hard")}
        ws, titles_txt = payload
        out = gemini_generate(gen_prompt_unanswerable(titles_txt, extra), max_tokens=512)
        return {"question_type": "unanswerable", "workspace_id": ws,
                "question": out.get("question", ""), "golden_answer": "",
                "gold_doc_ids": [], "gold_chunk_ids": [], "gold_passages": [],
                "expected_keywords": [], "difficulty": "medium"}

    log("  mẻ %d: sinh %d (single %d / multi %d / unans %d)..." % (
        batch_no, len(tasks), n_single, n_multi, n_unans))
    results = pmap(gen_one, tasks, label="gen")
    items = []
    for r in results:
        if not r or r.get("__error__") or not r.get("question"):
            continue
        id_seq[0] += 1
        prefix = {"single": "s", "multi": "m", "unanswerable": "u"}[r["question_type"]]
        r["id"] = "self-%s-%03d" % (prefix, id_seq[0])
        r["dataset"] = "self"
        r["provenance"] = {"source": "generated", "gen_model": "gemini-2.5-flash",
                           "batch": batch_no, "prompt_version": len(extra_rules),
                           "date": GEN_DATE}
        items.append(r)
    return items


# ---------------------------------------------------------------------------
# Verify 1 mẻ
# ---------------------------------------------------------------------------

def verify_batch(items):
    from common import gemini_generate

    def verify_one(it):
        if it["question_type"] == "unanswerable":
            # oracle: hệ thống thật retrieval + judge answerability phải là False
            st, body = http_json("POST", "/api/v1/rag/query/%d" % it["workspace_id"],
                                 {"question": it["question"], "top_k": 8}, timeout=120)
            ctx = body.get("context", "") if (st == 200 and isinstance(body, dict)) else ""
            if not ctx:
                return {"verdict": "pass", "reason": "ok"}
            ans = J.judge_answerability(it["question"], ctx)["answerable"]
            return ({"verdict": "pass", "reason": "ok"} if not ans
                    else {"verdict": "fail", "reason": "khong_suy_ra",
                          "note": "hóa ra trả lời được từ corpus"})
        out = gemini_generate(verify_prompt(it), system=VERIFIER_SYSTEM, max_tokens=512)
        v = out.get("verdict", "fail")
        return {"verdict": v if v in ("pass", "fail") else "fail",
                "reason": out.get("reason", "khac"), "note": out.get("note", "")[:200]}

    log("  verify %d item..." % len(items))
    verdicts = pmap(verify_one, items, label="verify")
    passed, failed, errors = [], [], 0
    for it, v in zip(items, verdicts):
        if not v or v.get("__error__"):
            errors += 1  # lỗi Gemini — KHÔNG tính là fail nội dung
            continue
        if v.get("verdict") == "pass":
            it["provenance"]["verifier_pass"] = True
            passed.append(it)
        else:
            reason = v.get("reason", "khac")
            failed.append((it, reason if reason in COUNTER_INSTRUCTIONS else "khac"))
    return passed, failed, errors


# ---------------------------------------------------------------------------
# Loop B chính
# ---------------------------------------------------------------------------

def run_loop(workspaces, batch_size, max_batches, target):
    os.makedirs(REVIEW_DIR, exist_ok=True)
    inv = load_inventory(workspaces)
    if not inv["chunks"]:
        log("❌ không có chunk nào — kiểm tra workspaces")
        return 2
    extra_rules = []
    id_seq = [0]
    for it in read_jsonl(POOL):
        id_seq[0] = max(id_seq[0], int(it["id"].split("-")[-1]))
    consec_ok = 0
    for b in range(1, max_batches + 1):
        items = gen_batch(inv, b, batch_size, extra_rules, id_seq)
        passed, failed, verr = verify_batch(items)
        judged = len(passed) + len(failed)  # mẫu có phán quyết thật (bỏ lỗi Gemini)
        rate = len(passed) / judged if judged else 0.0
        reasons = {}
        for _, r in failed:
            reasons[r] = reasons.get(r, 0) + 1
        log("  mẻ %d: %d sinh, %d judged, %d pass (%.0f%%) | %d lỗi-Gemini | fail: %s" % (
            b, len(items), judged, len(passed), rate * 100, verr, reasons or "—"))
        for it in passed:
            append_jsonl(POOL, it)
        append_jsonl(HISTORY, {"batch": b, "generated": len(items), "judged": judged,
                               "passed": len(passed), "pass_rate": round(rate, 3),
                               "gemini_errors": verr, "fail_reasons": reasons,
                               "prompt_rules": list(extra_rules), "date": GEN_DATE})
        if judged < max(5, batch_size // 4):
            log("  ⚠️  quá nhiều lỗi Gemini (chỉ %d/%d có phán quyết) — có thể do đua "
                "rate-limit; kết quả mẻ này không đáng tin" % (judged, len(items)))
        if rate >= target:
            consec_ok += 1
            if consec_ok >= 2:
                log("  ✅ đạt pass ≥ %.0f%% hai mẻ liên tiếp — dừng loop" % (target * 100))
                break
        else:
            consec_ok = 0
            # chỉnh prompt: thêm counter-instruction cho các lý do fail nổi bật
            for reason, cnt in sorted(reasons.items(), key=lambda x: -x[1]):
                instr = COUNTER_INSTRUCTIONS.get(reason)
                if instr and instr not in extra_rules:
                    extra_rules.append(instr)
                    log("  ➕ prompt rule: %s" % instr.strip("- "))
    pool = read_jsonl(POOL)
    log("  pool hiện có %d item pass — chạy tiếp: build_golden.py --review" % len(pool))
    return 0


# ---------------------------------------------------------------------------
# Review sheet + finalize
# ---------------------------------------------------------------------------

def make_review(target_counts={"single": 25, "multi": 15, "unanswerable": 10}, spare=10):
    pool = read_jsonl(POOL)
    if not pool:
        log("❌ pool rỗng — chạy --loop trước")
        return 2
    # dedupe theo embedding câu hỏi
    log("  dedupe %d item (embedding)..." % len(pool))
    embs = []
    for i in range(0, len(pool), 50):
        embs.extend(gemini_embed([it["question"] for it in pool[i:i + 50]]))
    keep = []
    for i, it in enumerate(pool):
        dup = any(cosine(embs[i], embs[j]) > 0.92 for j in keep)
        if not dup:
            keep.append(i)
    pool = [pool[i] for i in keep]
    log("  còn %d sau dedupe" % len(pool))
    # cân bằng loại + dự phòng
    random.shuffle(pool)
    chosen = []
    for t, n in target_counts.items():
        cand = [it for it in pool if it["question_type"] == t]
        chosen.extend(cand[:n + spare // len(target_counts)])
    # xuất sheet
    csv_path = os.path.join(REVIEW_DIR, "golden_self_review.csv")
    md_path = os.path.join(REVIEW_DIR, "golden_self_review.md")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "ws", "keep(Y/N)", "question", "golden_answer",
                    "edited_question", "edited_answer", "notes"])
        for it in chosen:
            w.writerow([it["id"], it["question_type"], it["workspace_id"], "Y",
                        it["question"], it["golden_answer"], "", "", ""])
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Duyệt golden set tự build (%d ứng viên)\n\n" % len(chosen))
        f.write("Sửa file CSV cùng tên: giữ = Y, loại = N; muốn sửa thì điền "
                "edited_question / edited_answer.\n\n")
        for it in chosen:
            f.write("## %s (%s, ws%d, %s)\n\n**Q:** %s\n\n**A:** %s\n\n" % (
                it["id"], it["question_type"], it["workspace_id"],
                it.get("difficulty", "?"), it["question"], it["golden_answer"] or "(unanswerable)"))
            for p in it["gold_passages"][:2]:
                f.write("> %s…\n\n" % p[:400].replace("\n", " "))
    log("  📄 %s (+ .md) — %d ứng viên chờ duyệt" % (csv_path, len(chosen)))
    return 0


def finalize(csv_path):
    pool = {it["id"]: it for it in read_jsonl(POOL)}
    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    out = []
    for row in rows:
        if (row.get("keep(Y/N)") or "").strip().upper() != "Y":
            continue
        it = pool.get(row["id"])
        if not it:
            continue
        if (row.get("edited_question") or "").strip():
            it["question"] = row["edited_question"].strip()
        if (row.get("edited_answer") or "").strip():
            it["golden_answer"] = row["edited_answer"].strip()
        it["provenance"]["reviewed"] = True
        out.append(it)
    with open(FINAL, "w", encoding="utf-8") as f:
        f.write("# golden_self.jsonl — bộ tự build đã qua Loop B + user duyệt (%s)\n" % GEN_DATE)
        for it in out:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    dist = {}
    for it in out:
        dist[it["question_type"]] = dist.get(it["question_type"], 0) + 1
    log("  ✅ golden_self.jsonl: %d item %s" % (len(out), dist))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspaces", default="1,3,4")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--batch-size", type=int, default=200)
    ap.add_argument("--max-batches", type=int, default=5)
    ap.add_argument("--target-pass", type=float, default=0.95)
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--finalize", metavar="CSV")
    args = ap.parse_args()
    ws = [int(w) for w in args.workspaces.split(",")]
    if args.loop:
        return run_loop(ws, args.batch_size, args.max_batches, args.target_pass)
    if args.review:
        return make_review()
    if args.finalize:
        return finalize(args.finalize)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
