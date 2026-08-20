#!/usr/bin/env python3
"""RAG quality eval grader — MiccoRAG-v3.

Reads a golden JSONL set, queries the live backend's retrieval endpoint
(`POST /api/v1/rag/query/{ws}`) and optionally the answer endpoint
(`POST /api/v1/rag/chat/{ws}`), then computes:
  - retrieval_hit_rate : câu hỏi có truy xuất được chunk (total_chunks > 0)
  - keyword_hit_rate   : tỉ lệ keyword kỳ vọng xuất hiện trong context
  - citation_rate      : câu trả lời có citation/nguồn
  - answer_ok_rate     : (nếu EVAL_ANSWER=1) câu trả lời không rỗng + chứa keyword
  - pass@1             : retrieval_ok AND keyword_ok AND (answer_ok nếu bật)

Zero external deps (stdlib urllib). Grounded stack: Gemini + ChromaDB, schema
RAGQueryResponse (total_chunks, chunks, context, citations).

Env: HARNESS_BASE_URL, EVAL_GOLDEN, EVAL_ANSWER=1, EVAL_MIN_PASS (default 0.6), EVAL_JSON
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("HARNESS_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
AUTH = {"Authorization": "Bearer dev-skip", "Content-Type": "application/json"}
HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.environ.get("EVAL_GOLDEN", os.path.join(HERE, "golden.jsonl"))
ANSWER = os.environ.get("EVAL_ANSWER", "0") == "1"
MIN_PASS = float(os.environ.get("EVAL_MIN_PASS", "0.6"))


def req(method, path, body=None, timeout=120):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, headers=AUTH, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None
    except Exception as e:
        return 0, str(e)


def load_golden(path):
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                items.append(json.loads(line))
    return items


def main():
    if not os.path.exists(GOLDEN):
        print(f"❌ Không thấy golden set: {GOLDEN}")
        return 2
    items = load_golden(GOLDEN)
    print(f"Golden set: {len(items)} mục | backend: {BASE} | answer-eval: {ANSWER}")
    print("─" * 74)
    res = []
    for it in items:
        q = it["question"]
        ws = it["workspace_id"]
        kws = [k.lower() for k in it.get("expected_keywords", [])]
        status, body = req("POST", f"/api/v1/rag/query/{ws}",
                           {"question": q, "top_k": it.get("top_k", 5)})
        ok = status == 200 and isinstance(body, dict)
        total = body.get("total_chunks", 0) if ok else 0
        ctx = (body.get("context", "") if ok else "").lower()
        cites = body.get("citations", []) if ok else []
        retrieval_ok = ok and total > 0
        kw_hit = (sum(1 for k in kws if k in ctx) / len(kws)) if kws else None
        kw_ok = (kw_hit is None) or (kw_hit > 0)
        cite_ok = len(cites) > 0
        ans_ok = None
        if ANSWER and retrieval_ok:
            s2, b2 = req("POST", f"/api/v1/rag/chat/{ws}", {"message": q}, timeout=120)
            ans = ""
            if s2 == 200 and isinstance(b2, dict):
                ans = b2.get("answer") or b2.get("content") or b2.get("message", "") or ""
            ans_ok = bool(ans and (not kws or any(k in ans.lower() for k in kws)))
        item_pass = retrieval_ok and kw_ok and (ans_ok in (None, True))
        res.append({"id": it.get("id"), "ws": ws, "status": status, "total_chunks": total,
                    "kw_hit": kw_hit, "cite": cite_ok, "ans_ok": ans_ok, "pass": item_pass})
        mark = "✅" if item_pass else "❌"
        kwtxt = "-" if kw_hit is None else f"{kw_hit:.0%}"
        line = (f"  {mark} [ws{ws}] chunks={total:<2} kw={kwtxt:<4} cite={'Y' if cite_ok else 'n'}"
                + (f" ans={'Y' if ans_ok else 'n'}" if ANSWER else "") + f"  {q[:46]}")
        print(line)

    n = len(res) or 1
    rate = lambda f: sum(1 for r in res if f(r)) / n
    retr = rate(lambda r: r["total_chunks"] > 0)
    cite = rate(lambda r: r["cite"])
    kw_vals = [r["kw_hit"] for r in res if r["kw_hit"] is not None]
    kwr = (sum(kw_vals) / len(kw_vals)) if kw_vals else 0.0
    p1 = rate(lambda r: r["pass"])
    print("─" * 74)
    print(f"  retrieval_hit_rate = {retr:.0%}")
    print(f"  keyword_hit_rate   = {kwr:.0%}  (trên {len(kw_vals)} mục có keyword)")
    print(f"  citation_rate      = {cite:.0%}")
    if ANSWER:
        print(f"  answer_ok_rate     = {rate(lambda r: r['ans_ok'] is True):.0%}")
    print(f"  pass@1             = {p1:.0%}  (ngưỡng {MIN_PASS:.0%})")
    out = {"base": BASE, "n": len(res), "retrieval_hit_rate": retr, "keyword_hit_rate": kwr,
           "citation_rate": cite, "pass_at_1": p1, "threshold": MIN_PASS, "items": res}
    jp = os.environ.get("EVAL_JSON")
    if jp:
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"  📄 report: {jp}")
    return 0 if p1 >= MIN_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
