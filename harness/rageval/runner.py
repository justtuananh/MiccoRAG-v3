#!/usr/bin/env python3
"""rageval/runner.py — benchmark runner / oracle cho MiccoRAG-v3.

4 phase, mỗi phase append JSONL vào RUN_DIR và RESUME idempotent (item đã có → bỏ qua):
  R retrieval : POST /rag/query  (per item × mode) — chunks + latency
  C chat      : POST /rag/chat   (per item × mode) — answer + sources + latency
  J judge     : correctness / claims+groundedness / answer-relevance / refusal /
                context-relevance (self thiếu gold_chunk_ids) / semantic_sim
  P report    : metrics per-item → aggregate → reports/rageval-<ts>.{json,md}

Env:
  RAGEVAL_DATASETS=self,hf   RAGEVAL_MODES=hybrid,vector_only   RAGEVAL_N=0
  RAGEVAL_PHASES=retrieval,chat,judge,report   RAGEVAL_RUN_DIR=cache/run-<ts>
  RAGEVAL_TOPK=8   RAGEVAL_SUBSET=<path.jsonl>  (ghi đè datasets)
  RAGEVAL_MIN_CORRECT=0.6   RAGEVAL_MIN_FAITHFUL=0.7
  RAGEVAL_JSON / RAGEVAL_MD  (đường dẫn report; mặc định harness/reports/)
"""
import json
import os
import re
import sys
import time

from common import (HERE, JsonlCache, cosine, gemini_embed, http_json, log, now_ts,
                    pmap, read_jsonl, append_jsonl, sha1, vi_tokenize)
import judge as J
import metrics as M

DATASET_FILES = {
    "self": os.path.join(HERE, "datasets", "golden_self.jsonl"),
    "hf": os.path.join(HERE, "datasets", "golden_hf.jsonl"),
}
REPORTS_DIR = os.path.join(os.path.dirname(HERE), "reports")

CFG = {
    "datasets": os.environ.get("RAGEVAL_DATASETS", "self,hf").split(","),
    "modes": os.environ.get("RAGEVAL_MODES", "hybrid,vector_only").split(","),
    "n": int(os.environ.get("RAGEVAL_N", "0")),
    "phases": os.environ.get("RAGEVAL_PHASES", "retrieval,chat,judge,report").split(","),
    "top_k": int(os.environ.get("RAGEVAL_TOPK", "8")),
    "min_correct": float(os.environ.get("RAGEVAL_MIN_CORRECT", "0.6")),
    "min_faithful": float(os.environ.get("RAGEVAL_MIN_FAITHFUL", "0.7")),
    "subset": os.environ.get("RAGEVAL_SUBSET", ""),
}

_emb_cache = JsonlCache(os.path.join(HERE, "cache", "emb-cache.jsonl"))


def embed_cached(text):
    key = sha1("emb", text[:4000])
    hit = _emb_cache.get(key)
    if hit is not None:
        return hit
    vec = gemini_embed([text[:4000]])[0]
    _emb_cache.put(key, vec)
    return vec


# ---------------------------------------------------------------------------
# Load items
# ---------------------------------------------------------------------------

def load_items():
    items = []
    if CFG["subset"]:
        items = read_jsonl(CFG["subset"])
    else:
        for ds in CFG["datasets"]:
            path = DATASET_FILES.get(ds.strip())
            if path and os.path.exists(path):
                items.extend(read_jsonl(path))
            elif path:
                log("  ⚠️  thiếu dataset %s (%s) — bỏ qua" % (ds, path))
    for it in items:
        it.setdefault("dataset", "self")
        it.setdefault("question_type", "single")
        it.setdefault("golden_answer", "")
        it.setdefault("gold_doc_ids", [])
        it.setdefault("gold_chunk_ids", [])
        it.setdefault("gold_passages", [])
        it.setdefault("gold_titles", [])
        it.setdefault("expected_keywords", [])
    if CFG["n"] > 0:
        # cắt giữ tỉ lệ loại câu hỏi: lấy round-robin theo type
        by_type = {}
        for it in items:
            by_type.setdefault(it["question_type"], []).append(it)
        out, i = [], 0
        while len(out) < CFG["n"] and any(by_type.values()):
            for t in list(by_type):
                if by_type[t] and len(out) < CFG["n"]:
                    out.append(by_type[t].pop(0))
        items = out
    return items


# ---------------------------------------------------------------------------
# Phase helpers (resume qua JSONL keyed id|mode)
# ---------------------------------------------------------------------------

def load_done(path):
    return {r["key"]: r for r in read_jsonl(path)}


def phase_retrieval(items, run_dir):
    path = os.path.join(run_dir, "retrieval.jsonl")
    done = load_done(path)
    todo = [(it, m) for it in items for m in CFG["modes"]
            if "%s|%s" % (it["id"], m) not in done]
    log("  [R] retrieval: %d call (đã có %d)" % (len(todo), len(done)))

    def run(pair):
        it, mode = pair
        t0 = time.time()
        status, body = http_json(
            "POST", "/api/v1/rag/query/%d" % it["workspace_id"],
            {"question": it["question"], "top_k": CFG["top_k"], "mode": mode},
            timeout=120)
        lat = time.time() - t0
        rec = {"key": "%s|%s" % (it["id"], mode), "id": it["id"], "mode": mode,
               "status": status, "latency": round(lat, 3), "chunks": [],
               "context_len": 0, "kg_summary": "", "total_chunks": 0}
        if status == 200 and isinstance(body, dict):
            rec["total_chunks"] = body.get("total_chunks", 0)
            rec["context_len"] = len(body.get("context", ""))
            rec["kg_summary"] = (body.get("knowledge_graph_summary") or "")[:2000]
            rec["context_head"] = (body.get("context") or "")[:6000]
            for ch in body.get("chunks", []):
                meta = ch.get("metadata") or {}
                cit = ch.get("citation") or {}
                doc_id = cit.get("document_id")
                if doc_id is None:
                    m = re.match(r"doc_(\d+)_chunk_", ch.get("chunk_id", ""))
                    doc_id = int(m.group(1)) if m else -1
                rec["chunks"].append({
                    "chunk_id": ch.get("chunk_id", ""),
                    "document_id": doc_id,
                    "heading_path": meta.get("heading_path", "") or " > ".join(
                        cit.get("heading_path", []) or []),
                    "content": (ch.get("content") or "")[:1500],
                    "score": ch.get("score", 0.0),
                })
        append_jsonl(path, rec)
        return rec

    pmap(run, todo, label="retrieval")
    return load_done(path)


def phase_chat(items, run_dir):
    path = os.path.join(run_dir, "chat.jsonl")
    done = load_done(path)
    todo = [(it, m) for it in items for m in CFG["modes"]
            if "%s|%s" % (it["id"], m) not in done]
    log("  [C] chat: %d call (đã có %d)" % (len(todo), len(done)))

    def run(pair):
        it, mode = pair
        t0 = time.time()
        status, body = http_json(
            "POST", "/api/v1/rag/chat/%d" % it["workspace_id"],
            {"message": it["question"], "mode": mode}, timeout=180)
        lat = time.time() - t0
        rec = {"key": "%s|%s" % (it["id"], mode), "id": it["id"], "mode": mode,
               "status": status, "latency": round(lat, 3), "answer": "",
               "sources": [], "kg_summary": ""}
        if status == 200 and isinstance(body, dict):
            rec["answer"] = body.get("answer") or ""
            rec["kg_summary"] = (body.get("kg_summary") or "")[:2000]
            for s in body.get("sources", []):
                rec["sources"].append({
                    "document_id": s.get("document_id"),
                    "content": (s.get("content") or "")[:1500],
                    "source_type": s.get("source_type", "vector"),
                    "heading_path": " > ".join(s.get("heading_path", []) or []),
                })
        append_jsonl(path, rec)
        return rec

    pmap(run, todo, label="chat")
    return load_done(path)


def phase_judge(items, run_dir, retr, chat):
    path = os.path.join(run_dir, "judge.jsonl")
    done = load_done(path)
    todo = [(it, m) for it in items for m in CFG["modes"]
            if "%s|%s" % (it["id"], m) not in done]
    log("  [J] judge: %d item×mode (đã có %d)" % (len(todo), len(done)))

    def run(pair):
        it, mode = pair
        key = "%s|%s" % (it["id"], mode)
        c = chat.get(key, {})
        r = retr.get(key, {})
        answer = c.get("answer", "")
        rec = {"key": key, "id": it["id"], "mode": mode}
        if not answer:
            rec["error"] = "no_answer"
            append_jsonl(path, rec)
            return rec
        # refusal
        rec["refusal_label"] = J.judge_refusal(answer)["label"]
        # correctness + semantic (chỉ câu answerable có đáp án chuẩn)
        if it["question_type"] != "unanswerable" and it["golden_answer"]:
            rec["llm_correct"] = J.judge_correctness(
                it["question"], it["golden_answer"], answer)["score"]
            try:
                rec["semantic_sim"] = round(cosine(
                    embed_cached(answer), embed_cached(it["golden_answer"])), 4)
            except Exception as e:
                rec["semantic_sim_err"] = str(e)[:120]
        # answer relevance
        rec["answer_relevance"] = J.judge_answer_relevance(it["question"], answer)["score"]
        # faithfulness so với context THẬT của lần chat (sources + kg_summary)
        if rec["refusal_label"] in ("attempt", "partial"):
            ctx = "\n\n".join(s["content"] for s in c.get("sources", []))
            if c.get("kg_summary"):
                ctx += "\n\n[KG] " + c["kg_summary"]
            claims = J.extract_claims(answer)["claims"]
            labels = J.judge_groundedness(claims, ctx)["labels"] if ctx else []
            rec["claims"] = claims
            rec["claim_labels"] = labels
        # context relevance cho item self thiếu gold_chunk_ids
        if (it["dataset"] == "self" and not it["gold_chunk_ids"]
                and it["question_type"] != "unanswerable" and r.get("chunks")):
            idx = J.judge_context_relevance(
                it["question"], it["golden_answer"],
                [ch["content"] for ch in r["chunks"]])["relevant_idx"]
            rec["ctx_relevant_idx"] = idx
        append_jsonl(path, rec)
        return rec

    pmap(run, todo, label="judge")
    return load_done(path)


# ---------------------------------------------------------------------------
# Per-item metric assembly
# ---------------------------------------------------------------------------

def _passage_overlap(chunk_content, passages, thresh=0.6):
    ct = set(vi_tokenize(chunk_content))
    for p in passages:
        pt = vi_tokenize(p)
        if pt and sum(1 for t in pt if t in ct) / len(pt) >= thresh:
            return True
    return False


def chunk_relevance(it, chunks, judged):
    """Trả (rels list bool theo rank, recall)."""
    rels = []
    if it["dataset"] == "hf" and it["gold_titles"]:
        # Docling KHÔNG giữ heading_path; tiêu đề bài nằm ở đầu content ("# Title").
        # Khớp theo: (a) tiêu đề gold xuất hiện trong content, (b) doc_id ∈ gold_doc_ids
        # + passage overlap, (c) passage overlap trực tiếp. Recall = số tiêu đề gold tìm thấy.
        titles = [t.lower() for t in it["gold_titles"]]
        gold_docs = set(it["gold_doc_ids"])
        found = set()
        for ch in chunks:
            body = (ch.get("heading_path", "") + " " + (ch.get("content") or "")).lower()
            hit_t = [t for t in titles if t and t in body]
            in_gold_doc = ch["document_id"] in gold_docs
            rel = bool(hit_t) or (in_gold_doc and _passage_overlap(
                ch["content"], it["gold_passages"], thresh=0.4)) or _passage_overlap(
                ch["content"], it["gold_passages"], thresh=0.5)
            if not hit_t and rel:
                for i, p in enumerate(it["gold_passages"]):
                    if _passage_overlap(ch["content"], [p], thresh=0.4) and i < len(titles):
                        hit_t.append(titles[i])
            found.update(hit_t)
            rels.append(rel)
        recall = M.context_recall(len(found), len(titles))
    elif it["gold_chunk_ids"]:
        gold = set(it["gold_chunk_ids"])
        rels = [ch["chunk_id"] in gold for ch in chunks]
        covered = {ch["chunk_id"] for ch in chunks if ch["chunk_id"] in gold}
        recall = M.context_recall(len(covered), len(gold))
    elif it["gold_doc_ids"]:
        gold_docs = set(it["gold_doc_ids"])
        rel_idx = set(judged.get("ctx_relevant_idx", []))
        rels = [(ch["document_id"] in gold_docs and i in rel_idx)
                for i, ch in enumerate(chunks)]
        covered = {ch["document_id"] for i, ch in enumerate(chunks) if rels[i]}
        recall = M.context_recall(len(covered), len(gold_docs))
    else:
        rels = [False] * len(chunks)
        recall = None
    return rels, recall


def build_rows(items, retr, chat, judged):
    rows = []
    for it in items:
        for mode in CFG["modes"]:
            key = "%s|%s" % (it["id"], mode)
            r, c, j = retr.get(key, {}), chat.get(key, {}), judged.get(key, {})
            row = {"id": it["id"], "dataset": it["dataset"], "mode": mode,
                   "question_type": it["question_type"],
                   "workspace_id": it["workspace_id"]}
            if r.get("status") != 200 or (c and c.get("status") not in (200, None)):
                if r.get("status") != 200 and c.get("status") != 200:
                    row["error"] = "http r=%s c=%s" % (r.get("status"), c.get("status"))
                    rows.append(row)
                    continue
            chunks = r.get("chunks", [])
            answerable = it["question_type"] != "unanswerable"
            if answerable and chunks is not None:
                rels, recall = chunk_relevance(it, chunks, j)
                row["hit_at_1"] = M.hit_at(rels, 1)
                row["hit_at_3"] = M.hit_at(rels, 3)
                row["hit_at_k"] = M.hit_at(rels, len(rels) or 1)
                row["mrr"] = M.mrr(rels)
                row["context_precision"] = M.context_precision(rels)
                row["context_recall"] = recall
            row["keyword_hit"] = M.keyword_hit(
                r.get("context_head", ""), it["expected_keywords"])
            row["query_latency"] = r.get("latency")
            row["chat_latency"] = c.get("latency")
            answer = c.get("answer", "")
            row["answer_chars"] = len(answer) if answer else None
            if answer and answerable and it["golden_answer"]:
                row["token_f1"] = M.token_f1(answer, it["golden_answer"])
                row["exact_match"] = M.exact_match(answer, it["golden_answer"])
                row["partial_match"] = M.partial_match(answer, it["golden_answer"])
            row["semantic_sim"] = j.get("semantic_sim")
            row["llm_correct"] = j.get("llm_correct")
            ar = j.get("answer_relevance")
            row["answer_relevance"] = (ar / 5.0) if ar else None
            row["faithfulness"] = M.faithfulness(j.get("claim_labels", []))
            row["refusal_label"] = j.get("refusal_label")
            srcs = c.get("sources", [])
            row["kg_source_rate"] = (
                sum(1 for s in srcs if s.get("source_type") == "kg") / len(srcs)
                if srcs else None)
            row["n_claims"] = len(j.get("claims", []) or [])
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def preflight():
    st, body = http_json("GET", "/health", timeout=10)
    if st != 200:
        log("❌ preflight: backend /health = %s" % st)
        return False
    from common import load_gemini_key
    try:
        load_gemini_key()
    except RuntimeError as e:
        log("❌ preflight: %s" % e)
        return False
    return True


def cleanup_history(items):
    for ws in sorted({it["workspace_id"] for it in items}):
        st, _ = http_json("DELETE", "/api/v1/rag/chat/%d/history" % ws, timeout=30)
        log("  🧹 xóa chat history ws%d → %s" % (ws, st))


def main():
    if not preflight():
        return 2
    items = load_items()
    if not items:
        log("❌ không có item nào (dataset thiếu?)")
        return 2
    run_dir = os.environ.get("RAGEVAL_RUN_DIR") or os.path.join(
        HERE, "cache", "run-%s" % now_ts())
    os.makedirs(run_dir, exist_ok=True)
    log("rageval: %d item × %d mode | run_dir=%s" % (len(items), len(CFG["modes"]),
                                                     os.path.relpath(run_dir, HERE)))
    with open(os.path.join(run_dir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(CFG, f, ensure_ascii=False, indent=1)

    phases = [p.strip() for p in CFG["phases"]]
    retr = (phase_retrieval(items, run_dir) if "retrieval" in phases
            else load_done(os.path.join(run_dir, "retrieval.jsonl")))
    chat = (phase_chat(items, run_dir) if "chat" in phases
            else load_done(os.path.join(run_dir, "chat.jsonl")))
    judged = (phase_judge(items, run_dir, retr, chat) if "judge" in phases
              else load_done(os.path.join(run_dir, "judge.jsonl")))
    if "chat" in phases:
        cleanup_history(items)
    if "report" not in phases:
        log("bỏ qua report (RAGEVAL_PHASES)")
        return 0

    rows = build_rows(items, retr, chat, judged)
    agg = M.aggregate(rows)
    ts = now_ts()
    out = {"timestamp": ts, "config": CFG, "n_items": len(items),
           "n_rows": len(rows),
           "n_errors": sum(1 for r in rows if r.get("error")),
           "aggregate": agg, "items": rows}
    os.makedirs(REPORTS_DIR, exist_ok=True)
    jpath = os.environ.get("RAGEVAL_JSON") or os.path.join(
        REPORTS_DIR, "rageval-%s.json" % ts)
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    log("  📄 JSON: %s" % jpath)
    import report as R
    mpath = os.environ.get("RAGEVAL_MD") or os.path.join(
        REPORTS_DIR, "rageval-%s.md" % ts)
    R.write_md(out, mpath)
    log("  📄 MD:   %s" % mpath)
    R.print_summary(out)

    # verdict theo ngưỡng (ưu tiên mode hybrid)
    mode = "hybrid" if "hybrid" in CFG["modes"] else CFG["modes"][0]
    g = agg.get("ALL|%s|ALL" % mode, {})
    cr, fa = g.get("correct_rate"), g.get("faithfulness")
    ok = True
    if cr is not None and cr < CFG["min_correct"]:
        log("  ❌ correct_rate %.2f < ngưỡng %.2f" % (cr, CFG["min_correct"]))
        ok = False
    if fa is not None and fa < CFG["min_faithful"]:
        log("  ❌ faithfulness %.2f < ngưỡng %.2f" % (fa, CFG["min_faithful"]))
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
