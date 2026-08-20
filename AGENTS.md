# AGENTS.md — miccoRAG v3

> Compiled from live code, not docs. See `CLAUDE.md` for exhaustive project memory.

## Project boundary

- **miccoRAG** = `micco-backend/` + `micco-frontend/` + `micco-server/`
- `everything-claude-code/` is an unrelated plugin project colocated in this repo. Ignore it when working on miccoRAG.

## Backend: single entry point

The `micco-backend` FastAPI app serves **everything** on one process:
- `/api/v1/*` — workspaces, documents, rag, config, expert
- `/api/*` — legacy compat routes (auth, admin, approvals, chat, knowledge, dashboard) — enabled when `COMPAT_ENABLE_LEGACY_ROUTES=true`

`micco-server/` is a **standalone legacy server** not needed in normal dev. Do not try to run both backends; use the single micco-backend app.

## Startup order matters

```bash
# 1. Infrastructure (PostgreSQL host 15435 + ChromaDB 8003)
cd micco-backend && docker compose -f docker-compose.services.yml up -d

# 2. Backend (port 8001 via run_bk.sh, or 8000 directly)
cd micco-backend/backend && uvicorn app.main:app --reload --port 8000

# 3. Frontend (port 5174, proxies /api to Cloudflare tunnel)
cd micco-frontend && npm run dev
```

Tables auto-create on startup (`AUTO_CREATE_TABLES=true`). Alembic migrations exist but are not required for dev.
Seed data: `python seed_data.py && python seed_users.py` from `micco-backend/backend/`.

## Port gotchas

- `run_bk.sh` starts on **port 8001** (dev, `--reload`). A **second** prod instance runs on **8000** (`--workers 2`, under `root`) — two backends coexist; `:8001` is the healthy dev one, `:8000` currently answers `/health` with 401.
- PostgreSQL: host **15435** → container 5432 (NOT 5435 — older docs drop the leading `1`).
- Frontend: **5174** (hardcoded in vite.config.js, not 5173).
- **Nginx drift**: `nginx.conf` proxies `/api` → `127.0.0.1:8089`, but no backend listens on 8089 (they're on 8001/8000). And `docker-compose.nginx.yml` uses `network_mode: host`, so `ports: 80:80` is ignored — nginx actually listens on **:8888** (`listen 8888`). Port `:80` on the box belongs to another project.

## Dev auth bypass

Set `VITE_SKIP_AUTH=true` in frontend env. This sends `token="dev-skip"` which the backend's `get_current_user()` accepts, returning the first DB user as Admin. No real login needed.

## Frontend API split

`src/utils/api.js` exports two fetch wrappers — know which to use:
- `ragFetch()` → legacy APIs under `/api/*` (auth, admin, approvals)
- `ragFetchV2()` → v2 APIs under `/api/v1/*` (workspaces, documents, RAG chat streaming)
- `readSSEStream()` → SSE/NDJSON parser for streaming chat

## Package manager

Frontend uses **pnpm** for install (`pnpm install`), **npm** for scripts (`npm run dev`, `npm run build`, `npm run lint`). Vite is the build tool.

## Commands

```bash
# Backend tests (pytest, asyncio_mode=auto)
cd micco-backend/backend && pytest tests/ -x --tb=short

# Frontend lint
cd micco-frontend && npm run lint

# Frontend build
cd micco-frontend && npm run build
```

## Harness system (`harness/`)

A multi-component harness verifies the project per layer. Entry: `bash harness/run.sh [COMPONENT|PRESET] [--json --md --paid]`. Each component prints `TỔNG: N PASS / M FAIL / K WARN`, exits non-zero on any FAIL, and only touches `nexusrag-*` / `micco-*` containers (safe on the shared VPS).

- **Components**: `smoke` (infra/health, = the old `harness_smoke.sh`, kept as a shim), `be` (ruff + pytest unit + coverage; integration opt-in), `fe` (eslint + `vite build` + Playwright e2e), `test` (all pytest suites), `qa` (gate → GO/NO-GO), `deploy` (deploy-verify, read-only), `eval` (RAG quality on `harness/eval/golden.jsonl`), `bench` (latency per search mode).
- **Presets**: `all` = smoke+be+fe+test+deploy (free, default); `full` = all + eval + bench; `qa` = gate.
- **Cost gating**: `RUN_EVAL=1` / `RUN_BENCH=1` / `RUN_E2E=1` / `RUN_INTEGRATION=1` / `RUN_RAG=1` (these call Gemini and/or need a live browser). `--paid` sets them all.
- **Domain subagents** (`.claude/agents/`): `backend`, `frontend`, `qa`, `deploy`, `test`, `eval`, `bench` (+ `harness-orchestrator`). These are full working, auto-routed subagents — when a task in a domain comes up, that agent does the work (implement/edit/test) **and** verifies with its harness component. Plus the `/harness` command. (The old root `backend-agent.md`/`frontend-agent.md`/`qa-agent.md` are now thin pointers to these.)

```bash
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh all --json'
ssh KMS 'RUN_EVAL=1 bash /home/kms/MiccoRAG-v3/harness/run.sh eval'
```

Reports land in `harness/reports/` (gitignored). Full ops runbook + known drift + security notes: **`OPERATIONS.md`**.

## Conventions that differ from defaults

- **async all the way**: every FastAPI endpoint is `async def`
- **Pydantic v2** only (no v1 syntax anywhere)
- **LLM access**: always via the factory (`get_llm_provider()`), never instantiate providers directly
- **ChromaDB is the vector store**: do not use FAISS/Pinecone/Qdrant unless asked
- **Cohere reranker** defaults for multilingual retrieval; falls back to raw vector search if `COHERE_API_KEY` is missing
- **React Router v7** with JSX (no TypeScript), files are `.jsx` not `.tsx`
- **No page-level error boundaries** implemented — the `.claude/rules/frontend.md` says "Error boundary cho mọi page" but this is aspirational, not actual

## Known landmines

1. `config.py` has **every field defined twice** (lines ~104-127 and ~129-153). Python uses the last value. Don't be confused by duplicate settings.
2. Documents stuck in PARSING/PROCESSING/INDEXING for >10min are auto-recovered to FAILED on restart.
3. Document upload flow requires both `status=INDEXED` and `approval_status=approved` for a doc to appear in queries. Non-admin uploads need explicit approval.
4. The `.claude/rules/frontend.md` describes Next.js/TypeScript patterns ("Next.js 14+ App Router", "TypeScript strict mode") that do **not** match this codebase (React + Vite, plain JSX).
