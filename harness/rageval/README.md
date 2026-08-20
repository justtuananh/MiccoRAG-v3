# harness/rageval — benchmark RAG đa tiêu chí cho MiccoRAG-v3

Component harness mới (gate `RUN_RAGEVAL=1`), zero-dep (stdlib + Gemini REST), đánh giá
hệ thống trên **2 dataset × 2 mode** với đầy đủ metric + 2 vòng lặp tối ưu.

## Metric

| Nhóm | Metric | Nguồn |
|---|---|---|
| Retrieval | hit@1/3/k, MRR, context_precision, context_recall, keyword_hit | `/rag/query` top_k=8; gold matching: HF theo `gold_titles` trong heading_path, self theo `gold_chunk_ids` (hoặc LLM context-relevance) |
| Answer | token-F1 (âm tiết VI), exact/partial match, semantic_sim (gemini-embedding), LLM-correct 1-5, answer_relevance | `/rag/chat` + judge |
| Hallucination | faithfulness (claim-level so với sources+kg của đúng lần chat), hallucinated_answer_rate, refusal_accuracy (câu unanswerable), false_refusal_rate | judge claims+groundedness+refusal |
| Latency | p50/p95 riêng query (retrieval) vs chat (end-to-end), per mode | đo wall-clock |
| GraphRAG | mọi metric Δ hybrid−vector_only (headline: subset multi-hop), kg_source_rate | chạy 2 mode |

## File

- `common.py` HTTP/Gemini/tokenize/cache/pmap · `metrics.py --selftest` · `judge.py --fixtures`
- `runner.py` 4 phase R→C→J→P, resume idempotent theo `RAGEVAL_RUN_DIR` · `report.py`
- `build_golden.py` Loop B (sinh→verify→refine, dừng pass≥95%×2 mẻ) → duyệt CSV → `datasets/golden_self.jsonl`
- `build_hf.py`→`translate.py`→`ingest_hf.py` HotpotQA→VI → ws `BENCH-HF-HotpotVI` → `datasets/golden_hf.jsonl`
- `optimize.py` Loop A (oracle subset 30 câu, 1 knob/vòng, ledger `cache/experiments.jsonl`,
  stop: 3 vòng ≤1% hoặc 30 vòng, rollback tự động, `.env` backup `.env.rageval-backup`)

## Chạy

```bash
# smoke (n=5, rẻ)
RUN_RAGEVAL=1 RAGEVAL_N=5 RAGEVAL_DATASETS=self RAGEVAL_MODES=hybrid bash harness/rageval.sh
# full benchmark
RUN_RAGEVAL=1 bash harness/rageval.sh          # hoặc: bash harness/run.sh full --paid
# re-judge không tốn chat (resume)
RUN_RAGEVAL=1 RAGEVAL_RUN_DIR=harness/rageval/cache/run-<ts> RAGEVAL_PHASES=judge,report bash harness/rageval.sh

# Loop B — build bộ tự build
python3 build_golden.py --workspaces 1,3,4 --loop && python3 build_golden.py --review
#   → duyệt datasets/review/golden_self_review.csv → python3 build_golden.py --finalize <csv>

# Bộ HF
python3 build_hf.py --n 130 && python3 translate.py --in datasets/review/hf_work
python3 ingest_hf.py --in datasets/review/hf_work --dry-run   # rồi --apply (~1-2h)

# Loop A — tối ưu config
python3 optimize.py make-subset && python3 optimize.py baseline
python3 optimize.py apply-and-run --set NEXUSRAG_RERANKER_TOP_K=10 --hypothesis "..."
python3 optimize.py status   # lịch sử + stop-rule
python3 optimize.py restore --best   # hoặc --original
```

## Schema dataset (JSONL, dòng `#` = comment)

`id, dataset(self|hf), workspace_id, question, golden_answer(""=unanswerable),
question_type(single|multi|unanswerable), gold_doc_ids[], gold_chunk_ids[],
gold_passages[], gold_titles[](hf), expected_keywords[], difficulty, provenance{}`

## Lưu ý an toàn

- Gemini key đọc server-side từ `micco-backend/backend/.env` — không bao giờ in.
- Concurrency ≤4 (VPS chung, backend tự fan-out Gemini). Sau run tự xóa chat history các ws đã đụng.
- `optimize.py` chỉ sửa dòng `NEXUSRAG_*` trong `.env` (backup 1 lần đầu); knob chunk-size là
  ĐẮT (cần re-ingest ws bench). Reload = touch `app/main.py` (uvicorn --reload). Không đụng prod :8000.
- Teardown ws benchmark: `DELETE /api/v1/workspaces/{id}` (xóa sạch Chroma+KG+DB).
