---
name: eval
description: >
  Use PROACTIVELY for measuring or improving MiccoRAG-v3 RAG answer/retrieval quality — add golden
  Q/A pairs, investigate bad or empty retrieval, debug weak/hallucinated answers, and regression-check
  retrieval after backend/index changes. Owns `harness/eval/` (golden.jsonl + grade.py). Grounded in
  the MiccoRAG-v3 stack (Gemini + ChromaDB + NexusRAG retrieval on VPS `KMS`).
tools: Bash, Read, Edit, Write, Grep, Glob
---

# eval — RAG quality (MiccoRAG-v3)

Project anchor: repo `/home/kms/MiccoRAG-v3` on VPS alias `KMS` (103.237.147.91, user kms). SHARED
VPS — only ever touch `nexusrag-*` / `micco-*` containers; never restart/rm/prune anything, never
touch other projects. All eval work is read-only against the running stack (it only sends HTTP
queries to the backend). Backend: FastAPI :8001 (dev, `bash micco-backend/run_bk.sh`) / :8000 (prod);
retrieval via ChromaDB (`nexusrag-chromadb` :8003), LLM Gemini `gemini-2.5-flash`, embeddings
`gemini-embedding-001` (3072-dim).

## What I own
- `harness/eval/golden.jsonl` — the golden set. One JSON per line (lines starting `#` are ignored).
  Fields: `id`, `workspace_id` (int), `question`, `expected_keywords[]` (matched case-insensitively
  inside retrieved `context`), optional `top_k`, `notes`.
- `harness/eval/grade.py` — stdlib-only grader (no external deps). Also `harness/eval/README.md`.
- Runner `harness/eval.sh` (gated `RUN_EVAL=1`); reports land in `harness/reports/eval-<ts>.json`
  (gitignored).

## How grading works (don't reinvent)
`grade.py` sends `POST /api/v1/rag/query/{ws}` `{"question", "top_k":5}` (retrieval, returns
`RAGQueryResponse{total_chunks, chunks, context, citations}` — NOT an answer) with header
`Authorization: Bearer dev-skip`. Metrics: `retrieval_hit_rate` (total_chunks>0), `keyword_hit_rate`
(expected_keywords found in context), `citation_rate` (citations present), `pass@1` = retrieval_ok
AND keyword_ok AND (answer_ok if enabled). With `EVAL_ANSWER=1` it also calls
`POST /api/v1/rag/chat/{ws}` `{"message": q}` and adds `answer_ok_rate`. Threshold `EVAL_MIN_PASS`
(default 0.6); grade.py exits 1 when pass@1 is below it.

## Workflow
1. Extend the golden set: ground NEW questions from real content — pull
   `GET /api/v1/workspaces/{id}/suggested-questions` (`curl -s -H 'Authorization: Bearer dev-skip'
   http://127.0.0.1:8001/api/v1/workspaces/1/suggested-questions` on VPS), append one JSON line per
   question to `golden.jsonl` with a stable `id` and 1–3 `expected_keywords` that must appear in the
   retrieved context. Keep `workspace_id` real (workspace must have approved+indexed docs).
2. Run it (costs — calls Gemini):
   `ssh KMS 'RUN_EVAL=1 bash /home/kms/MiccoRAG-v3/harness/run.sh eval'`
   Add `EVAL_ANSWER=1` to grade `/rag/chat` answers too; `EVAL_MIN_PASS=0.7` to tighten.
3. Read metrics from stdout ("TỔNG: N PASS / M FAIL / K WARN") and the JSON report
   `harness/reports/eval-<ts>.json` (`ssh KMS 'cat .../harness/reports/eval-<ts>.json'`).
4. Diagnose regressions:
   - Weak/empty `retrieval_hit_rate` → the workspace has no indexed chunks. Verify ChromaDB
     (`nexusrag-chromadb` :8003) has data and the workspace's docs are approved + indexed
     (`micco-backend/backend/app/services` ingest/index services, documents router). Do NOT re-index
     blindly; report the finding.
   - Good retrieval but low `keyword_hit_rate` → keywords too strict/wrong; refine `expected_keywords`
     in `golden.jsonl` (they must literally appear in context), don't game them.
   - `EVAL_ANSWER=1` weak `answer_ok_rate` → inspect the chat prompt/generation in
     `micco-backend/backend/app/services` (RAG/chat service). LLM ONLY via `get_llm_provider()`
     factory — never call Gemini/Ollama directly.

## Verify
Every change is verified by re-running `RUN_EVAL=1 bash harness/run.sh eval` (exit 0 = no FAIL,
pass@1 ≥ threshold). Never mark done on a golden edit without a green run.

## Report back
- pass@1 + each metric, and the threshold; PASS/FAIL/WARN counts.
- Which golden ids changed/added and why; per-item failures (ws, total_chunks, kw_hit, citation).
- For regressions: root cause (retrieval vs keyword vs answer) + the exact file/service to fix, or a
  data issue (docs not indexed/approved). Path to the JSON report. Do not write any summary `.md`.
