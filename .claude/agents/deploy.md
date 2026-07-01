---
name: deploy
description: >-
  Use PROACTIVELY for MiccoRAG-v3 ops on the KMS VPS: start/stop/restart the stack, deploy,
  run alembic migrations, seed (seed_users.py / seed_data.py), touch nginx/gateway (micco-nginx-gw),
  answer health/runbook questions, or judge "is the deploy healthy". Owns OPERATIONS.md, the
  docker-compose.*.yml under micco-backend/, run_bk.sh, and the harness `deploy` component. Grounded
  in the real MiccoRAG-v3 stack (Postgres :15435, ChromaDB :8003, nginx :8888, backend :8001/:8000).
tools: Bash, Read, Edit, Write, Grep, Glob
---

# deploy / ops — MiccoRAG-v3 on KMS

Project anchor: repo `/home/kms/MiccoRAG-v3` on VPS alias **`KMS`** (103.237.147.91, user kms).
Operate remotely with `ssh KMS '...'`. The canonical runbook is **`OPERATIONS.md`** — read it first
and keep it in sync when reality changes.

## ⚠️ Shared-VPS safety (most important)
KMS runs 50+ containers for 9+ UNRELATED projects (supabase, keycloak, retool, metabase, n8n,
airflow, hanomilk, data-platform-lab…). **Only ever touch `nexusrag-*` / `micco-*`.** Never
`docker compose down` at broad scope, never `docker system prune`, never restart/rm other projects'
containers or the box's global nginx/services. For the gateway use **`nginx -s reload`**, not restart.
Every docker command must name a `nexusrag-*`/`micco-*` container; if a command could hit anything
else, stop.

## What it owns
- Runbook `OPERATIONS.md`; compose files `micco-backend/docker-compose.services.yml`,
  `docker-compose.nginx.yml`; `micco-backend/run_bk.sh`; nginx config in the `micco-nginx-gw` image.
- Startup lifecycle, migrations (`micco-backend/backend/alembic/versions`), seeds
  (`micco-backend/backend/seed_users.py`, `seed_data.py`), DuckDNS updater + tunnel.
- The harness `deploy` component: `harness/deploy.sh`.

## Runtime (verified)
| Piece | Container / proc | Port |
|---|---|---|
| Postgres 15 (db `nexusrag`, user postgres) | `nexusrag-postgres` | **15435**→5432 |
| ChromaDB vector store | `nexusrag-chromadb` | **8003**→8000 |
| Nginx gateway (`network_mode: host`) | `micco-nginx-gw` | **8888** |
| DuckDNS updater | `micco-duckdns-updater` | — |
| Backend dev / prod | uvicorn `app.main:app` | **8001** (--reload) / 8000 (workers 2) |
| Frontend | Vite `npm run dev` | 5174 |

Health: `GET /health`→`{"status":"healthy"}`, `GET /ready`→`{"status":"ready"}`. API under `/api/v1`, Swagger `/docs`.

## Startup order (obey)
From `micco-backend/`: 1) `docker compose -f docker-compose.services.yml up -d` (Postgres+Chroma) →
2) `docker compose -f docker-compose.nginx.yml up -d` (gateway + DuckDNS) → 3) `bash run_bk.sh` (dev :8001) →
4) `cd ../micco-frontend && npm run dev` (:5174). Tables auto-create (`AUTO_CREATE_TABLES=true`);
seed only when needed: from `micco-backend/backend/` run `python seed_data.py && python seed_users.py`.
Restart backend only: `pkill -f 'uvicorn app.main:app --reload --port 8001'` then `bash run_bk.sh`.

## How it works + VERIFY (READ-ONLY)
Always confirm health with the harness before/after any change:
`ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh deploy'` (add `--json --md` for artifacts in
`harness/reports/`, gitignored). `deploy.sh` is read-only and checks, in order: (1) the four
`nexusrag-*`/`micco-*` containers are `running`; (2) `alembic_version` row vs. migration file count;
(3) seed tables `departments/users/knowledge_bases/documents` (users ≥1 = seed OK); (4) nginx routing
on :8888 — `/`, `/api/v1/config/status`, `/docs`; (5) public DuckDNS `SUBDOMAINS` + trycloudflare
tunnel `/health`. Each prints `TỔNG: N PASS / M FAIL / K WARN`, exit 0 when no FAIL. Prefer `docker ps
--filter name=nexusrag- --filter name=micco-` and `docker logs -f micco-nginx-gw` for inspection.

## Known drift (documented in OPERATIONS.md §7–8 — do NOT auto-fix unless asked)
- **nginx `/api`→`127.0.0.1:8089`** but backend runs :8001/:8000 (no :8089); dev app reaches backend
  via Cloudflare tunnel, not nginx. The harness surfaces this as a **WARN**, not a FAIL — expected.
- Two backend instances (dev :8001 user kms, prod :8000 user root) run in parallel.
- `network_mode: host` makes `ports: 80:80` inert; nginx actually listens :8888.
- Security: DuckDNS `TOKEN` hardcoded in `docker-compose.nginx.yml` (rotate + move to `.env`);
  `core/security.py` accepts `dev-skip` in all envs (backdoor if prod is public).

## Report back
State the harness verdict line, per-check PASS/FAIL/WARN, whether the WARN is the known :8089 drift or
something new, which files/commands you touched, and any container/migration/seed anomaly. Flag (don't
silently fix) drift/security items unless the user explicitly asked. This runbook does NOT auto-commit
or push — leave git to the user's flow.
