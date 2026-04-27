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
# 1. Infrastructure (PostgreSQL 5435 + ChromaDB 8003)
cd micco-backend && docker compose -f docker-compose.services.yml up -d

# 2. Backend (port 8001 via run_bk.sh, or 8000 directly)
cd micco-backend/backend && uvicorn app.main:app --reload --port 8000

# 3. Frontend (port 5174, proxies /api to Cloudflare tunnel)
cd micco-frontend && npm run dev
```

Tables auto-create on startup (`AUTO_CREATE_TABLES=true`). Alembic migrations exist but are not required for dev.
Seed data: `python seed_data.py && python seed_users.py` from `micco-backend/backend/`.

## Port gotchas

- `run_bk.sh` starts on **port 8001** (not 8000 as README says). Check the Vite proxy target in `vite.config.js` matches.
- PostgreSQL: **5435** (not default 5432).
- Frontend: **5174** (hardcoded in vite.config.js, not 5173).

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
