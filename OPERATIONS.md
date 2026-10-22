# OPERATIONS.md — Vận hành MiccoRAG-v3 trên VPS `KMS`

> Runbook vận hành cho **MiccoRAG-v3**. Kèm harness kiểm chứng, thứ tự khởi động,
> thao tác thường dùng, các điểm lệch cấu hình đã biết và cảnh báo bảo mật.
> Xem thêm: [`README.md`](README.md) · [`.claude/CLAUDE.md`](.claude/CLAUDE.md) · [`AGENTS.md`](AGENTS.md)

---


## Cấu hình triển khai 30/09/2026

Đợt cập nhật này dùng thư mục `/home/micco/MiccoRAG-v3`, tài khoản dịch vụ `micco` (UID1001). Các ví dụ `kms` trong phần cũ bên dưới là thông tin lịch sử; đối chiếu môi trường trước khi chạy. Chỉ quản lý backend8001, frontend5174 và gateway8888; không thao tác tiến trình8000 hoặc dịch vụ của dự án khác.

- Backend và frontend giữ nguyên địa chỉ lắng nghe hiện tại. Gateway chuyển tiếp tới frontend Vite trên5174; build được kiểm riêng, không gọi runtime này là phục vụ bundle tĩnh.
- PostgreSQL `nexusrag-postgres` và ChromaDB `nexusrag-chromadb` dùng `restart: unless-stopped` trong Compose và trên container. Gateway giữ `always`. Docker và cron đã bật khi máy khởi động.
- Watchdog `harness/ops/runtime_supervisor.py` chạy bằng user `micco` qua crontab `@reboot` và mỗi phút. Nó nhận diện đúng cổng/cwd/executable trước khi nhận quản lý tiến trình, chỉ tạo tiến trình thiếu, không giết tiến trình lạ. Khởi động ứng dụng dùng môi trường riêng trong `/home/micco/.config/miccorag/{backend,frontend}-env.json` (0600), cấu hình watchdog `supervisor.json` (0600). Giữ đường dẫn Python virtualenv, không thay bằng đường dẫn đích của symlink.
- Cờ `/home/micco/.local/state/miccorag/deploy-maintenance` ngăn watchdog khởi động giữa đợt triển khai/khôi phục. Chỉ bỏ cờ sau khi bản triển khai hoặc bản khôi phục đạt health/readiness. Trạng thái watchdog ở `state.json` cùng thư mục; log được bảo vệ trong `/home/micco/logs/miccorag/`.
- Kiểm tra sau cập nhật: `/health` và `/ready` trên8001; giao diện5174; gateway8888 và `/health` qua gateway. Chạy `bash harness/run.sh deploy --json --md`; đọc rõ từng WARN, không coi chưa có lịch sử Alembic là đã chạy đầy đủ mọi migration cũ.
- DB cũ được tạo qua ORM, chưa có `alembic_version`. Các patch007–010 được áp theo thứ tự trong một transaction, kiểm giữ nguyên số dòng và các cột/FK/index mới. Nhật ký migration và manifest phát hành là căn cứ; không tự stamp toàn bộ lịch sử migration chưa kiểm chứng.
- Graph được dựng từ markdown thuộc đúng KB, lưu bản sao độc lập và đối chiếu SHA/ID trước khi thay trong cửa sổ bảo trì. Giới hạn mặc định:200nút/500cạnh mỗi lượt xem, độ sâu4;2000tài liệu/20000nút/50000cạnh/256MiB cho mỗiKB; tối đa8 namespace mỗi worker. Cảnh báo từ80%; ngưỡng RSS1,5GiB là kiểm tra tiếp nhận công việc, không phải giới hạn bộ nhớ cứng của hệ điều hành. Nếu graph chạm ngưỡng, truy xuất vector vẫn được dùng; API duyệt graph báo không khả dụng thay vì trả rỗng như thể không có dữ liệu. Cấu hình nằm trong `app/core/config.py`.
- Backup được người dùng chấp nhận đóng hạng mục ngày30/09/2026. Không diễn giải quyết định này thành bằng chứng lịch backup hằng ngày đã hoạt động. Không reboot VPS dùng chung để thử; kiểm khởi động/phục hồi dùng tiến trình và thư mục cô lập.

Kết quả thực thi, trạng thái triển khai và các giới hạn hiện tại nằm trong `evaluation/runs/20260930-deploy/` ở workspace đánh giá. Bản rollback trên máy chủ được giữ riêng, có kiểm hash và hạn chế quyền đọc; không đưa thông tin đăng nhập vào báo cáo.


## 1. Truy cập

| Mục | Giá trị |
|---|---|
| SSH alias | `KMS` |
| Host / user | `103.237.147.91` / `kms` |
| Thư mục dự án | `/home/kms/MiccoRAG-v3` |
| Backend | `/home/kms/MiccoRAG-v3/micco-backend` |
| Frontend | `/home/kms/MiccoRAG-v3/micco-frontend` |

```bash
ssh KMS                       # vào VPS
cd /home/kms/MiccoRAG-v3
```

---

## 2. ⚠️ AN TOÀN — VPS DÙNG CHUNG

`KMS` là **box dùng chung**, chạy 50+ container của **9+ dự án không liên quan**.
**CHỈ được đụng vào stack MiccoRAG.** Tuyệt đối không restart/xóa/prune container
của dự án khác, không `docker system prune`, không sửa nginx/service toàn cục.

**✅ Của MiccoRAG (được phép thao tác):**
- Container: `nexusrag-postgres`, `nexusrag-chromadb`, `micco-nginx-gw`, `micco-duckdns-updater`
- Tiến trình: uvicorn backend (`:8001` dev, `:8000` prod), Vite frontend (`:5174`)
- Mã nguồn & dữ liệu dưới `/home/kms/MiccoRAG-v3`, DB `nexusrag` (Postgres :15435)

**⛔ TUYỆT ĐỐI KHÔNG đụng (dự án khác trên box):**
- `supabase` (13 container), `keycloak`, `retool`, `metabase`, `n8n`, `airflow`
- `hanomilk/*`, `data-platform-lab` (Kafka/Spark/Hive), `mobiwork_pipeline`
- Mọi Postgres/Redis/Minio/Kafka khác (5432, 7179, 32778…, 9092, 2181…)
- **Không** dùng `docker compose down` ở phạm vi rộng; luôn chỉ định `-f <file>` của MiccoRAG.

> Quy tắc: **lệnh docker phải nêu đích danh container `nexusrag-*` / `micco-*`.**
> Nếu một lệnh có thể ảnh hưởng container khác → dừng lại.

---

## 3. Kiến trúc runtime (thực tế đã xác minh)

| Thành phần | Chi tiết | Cổng |
|---|---|---|
| Backend (FastAPI) — **dev** | `run_bk.sh` → `uvicorn app.main:app --reload --port 8001` (user `kms`) | **8001** |
| Backend (FastAPI) — **prod** | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2` (user `root`) | 8000 |
| Frontend (React 19 + Vite 7) | `npm run dev` | 5174 |
| PostgreSQL 15 | container `nexusrag-postgres`, db `nexusrag`, user `postgres` | **15435** → 5432 |
| ChromaDB | container `nexusrag-chromadb` (vector store) | 8003 → 8000 |
| Nginx gateway | container `micco-nginx-gw`, `network_mode: host`, **lắng nghe :8888** | **8888** |
| DuckDNS updater | container `micco-duckdns-updater` | — |

Health: `GET /health` → `{"status":"healthy"}` · `GET /ready` → `{"status":"ready"}`
API: `/api/v1/{workspaces,documents,rag,config,expert}` · Swagger `/docs`.

---

## 4. Khởi động (đúng thứ tự)

```bash
cd /home/kms/MiccoRAG-v3/micco-backend

# 1) Hạ tầng: PostgreSQL (:15435) + ChromaDB (:8003)
docker compose -f docker-compose.services.yml up -d

# 2) Nginx gateway (+ DuckDNS)
docker compose -f docker-compose.nginx.yml up -d

# 3) Backend — dev (auto-reload, :8001)
bash run_bk.sh
#    hoặc prod (:8000, 2 workers) — chạy trong tmux/screen:
#    cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# 4) Frontend (Vite dev, :5174)
cd ../micco-frontend && npm run dev
```

Bảng tự tạo khi backend khởi động (`AUTO_CREATE_TABLES=true`).
Seed dữ liệu (chỉ khi cần): từ `micco-backend/backend/` chạy `python seed_data.py && python seed_users.py`.

---

## 5. Harness đa-thành-phần (`harness/`)

Hệ harness thống nhất kiểm chứng toàn dự án theo từng thành phần. Entry: **`harness/run.sh`**.
Mọi component in `TỔNG: N PASS / M FAIL / K WARN`, **exit 0 khi không FAIL** (hợp cron/CI),
và **chỉ đụng container `nexusrag-*`/`micco-*`** (an toàn trên VPS dùng chung).

```bash
# Chạy nhiều component (mặc định preset 'all' = smoke+be+fe+test+deploy — miễn phí)
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh all --json'

# Một component cụ thể
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh smoke'      # hạ tầng/health
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh qa'         # cổng chất lượng → GO/NO-GO

# Các tầng TỐN PHÍ (gọi Gemini) — phải bật cờ:
ssh KMS 'RUN_EVAL=1  bash /home/kms/MiccoRAG-v3/harness/run.sh eval'
ssh KMS 'RUN_BENCH=1 bash /home/kms/MiccoRAG-v3/harness/run.sh bench'
ssh KMS 'RUN_E2E=1   bash /home/kms/MiccoRAG-v3/harness/run.sh fe'     # Playwright e2e
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh full --paid'       # tất cả, kể cả eval+bench
```

| Component | Kiểm | Ghi chú |
|---|---|---|
| **smoke** | Docker/Postgres/Chroma/backend health/API/nginx/frontend | = `harness_smoke.sh` (giữ shim tương thích) |
| **be** | ruff (nếu có) + pytest backend unit + coverage; integration opt-in | `RUN_INTEGRATION=1` (tốn Gemini) |
| **fe** | eslint (WARN) + `vite build` (bắt buộc) + Playwright e2e | `RUN_E2E=1` |
| **test** | pytest backend + micco-server (legacy WARN-skip nếu thiếu langgraph) | `RUN_INTEGRATION=1` |
| **qa** | gate: smoke+be+fe+test → 🟢 GO / 🔴 NO-GO | |
| **deploy** | containers/migrations/seed/nginx routing/public — READ-ONLY | báo WARN drift nginx→:8089 |
| **eval** | chất lượng RAG trên golden set (retrieval/keyword/citation/pass@1) | `RUN_EVAL=1`; golden ở `harness/eval/` |
| **bench** | latency p50/p95 theo mode (hybrid/vector_only/naive) | `RUN_BENCH=1`; report `harness/reports/` |

Artifact: `--json`/`--md` ghi vào `harness/reports/<ts>.*` (đã gitignore).
Mỗi lĩnh vực có một **subagent chuyên trách, tự-động-định-tuyến** trong `.claude/agents/`
(`backend`, `frontend`, `qa`, `deploy`, `test`, `eval`, `bench` + `harness-orchestrator`) —
làm việc đầy đủ (implement/sửa + test) rồi verify bằng harness. Kèm lệnh `/harness`.
Xem thêm README mục "Kiểm thử & Harness".

---

## 6. Thao tác thường dùng

```bash
# Trạng thái container của MiccoRAG (lọc để không đụng dự án khác)
docker ps --filter name=nexusrag- --filter name=micco-

# Log hạ tầng
cd /home/kms/MiccoRAG-v3/micco-backend
docker compose -f docker-compose.services.yml logs -f postgres
docker compose -f docker-compose.services.yml logs -f chromadb
docker logs -f micco-nginx-gw

# Vào Postgres
docker exec -it nexusrag-postgres psql -U postgres -d nexusrag

# Khởi động lại CHỈ backend dev: dừng tiến trình uvicorn :8001 rồi chạy lại run_bk.sh
pkill -f 'uvicorn app.main:app --reload --port 8001'   # (thận trọng: chỉ tiến trình dev của kms)
bash run_bk.sh
```

---

## 7. Điểm lệch cấu hình đã biết (chưa sửa — chỉ theo dõi)

| # | Vấn đề | Hiện trạng | Gợi ý xử lý |
|---|---|---|---|
| 1 | **Nginx → backend lệch cổng** | `nginx.conf`: `/api` proxy `127.0.0.1:8089`, nhưng backend chạy `:8001`/`:8000` (không có :8089) | Sửa `proxy_pass` về cổng backend thật, hoặc chạy backend ở :8089 |
| 2 | **2 instance backend** | dev `:8001` (user kms) và prod `:8000` (user root) chạy song song | Chọn 1 instance chuẩn cho prod, tắt cái còn lại |
| 3 | **Nginx cổng lắng nghe** | `network_mode: host` → `ports: 80:80` vô hiệu; nginx thực sự nghe `:8888` (theo `nginx.conf`) | Thống nhất tài liệu; `:80` trên box là dự án khác |
| 4 | **Tên port Postgres** | Host port thật là **15435** (tài liệu cũ ghi "5435") | Đã sửa trong README/CLAUDE.md/AGENTS.md |
| 5 | **Header compose** | `docker-compose.services.yml` mở đầu ghi "MiccoRAG-v2" | Sửa comment cho đúng v3 |

---

## 8. ⚠️ Cảnh báo bảo mật (khuyến nghị, chưa tự sửa)

- **DuckDNS TOKEN lộ trong git:** `micco-backend/docker-compose.nginx.yml` hardcode
  `TOKEN=<...>` làm giá trị mặc định của biến. → Chuyển sang `.env` (đã gitignore) và
  **xoay token** trên DuckDNS.
- **Dev auth bypass luôn bật:** `core/security.py` chấp nhận token `dev-skip` (trả về
  user đầu tiên/Admin) **không phụ thuộc môi trường**. Ổn cho dev, nhưng nếu instance
  prod (:8000/:8089) mở ra Internet thì đây là backdoor — nên chặn `dev-skip` khi
  không phải môi trường dev.

---

## 9. Git & triển khai

Repo là git tại `/home/kms/MiccoRAG-v3` (branch phát triển chính). Sau khi review các
thay đổi (harness + tài liệu), tự commit theo quy trình của bạn. Runbook này **không**
tự động commit/push.

## Runtime update — 2026-09-29 (user micco)

Current checkout: `/home/micco/MiccoRAG-v3`, SSH `micco@103.237.147.91`.
This snapshot supersedes the older kms paths and runtime/drift notes above.

- Started existing `nexusrag-postgres` and `nexusrag-chromadb` containers with `docker start`; existing data retained.
- Backend: detached screen `micco-backend`, working directory `micco-backend/backend`, command `/home/micco/MiccoRAG-v3/micco-backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001`.
- Frontend: detached screen `micco-frontend`, working directory `micco-frontend`, command `/home/micco/node22/bin/node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5174`.
- Screen logs: `/home/micco/logs/miccorag/backend.log` and `/home/micco/logs/miccorag/frontend.log`.
- Inspect with `screen -ls`; attach with `screen -r micco-backend` or `screen -r micco-frontend`; detach with Ctrl+A then D. These processes survive terminal/SSH disconnect, but are not configured to restart after VPS reboot or process failure.
- Gateway `:8888` routes frontend to `:5174` and API to `:8001`. Port `:8000` belongs to Supabase Kong, not this checkout.
- Verified via fresh SSH connections: backend health/ready, frontend, gateway frontend/API/docs all HTTP 200.
- `BACKEND_PORT=8001 RUN_RAG=0 bash harness/run.sh smoke deploy --json --md`: 20 PASS / 2 FAIL / 3 WARN. Both FAILs refer to the same missing optional `micco-duckdns-updater`; WARNs: dev-skip rejected (401), paid RAG query skipped, no Alembic version row. No seed or manual migration run.
- Reports: `harness/reports/20260929-152849.{json,md}`. Full RAG chat not exercised by this startup check.

## Management KB access update — 2026-09-29

- Activated the management read/retrieval permission change by gracefully restarting only the backend on `127.0.0.1:8001`, retaining its command, working directory, application environment, and `/home/micco/logs/miccorag/backend.log`. New detached screen: `824312.micco-backend`; frontend screen `456011.micco-frontend` unchanged.
- Verified `/health` and `/ready` healthy/ready, plus live authenticated workspace list, summary, and detail endpoints: both `Giám đốc` and `Phó giám đốc` can access all 7 KB; a `Nhân viên` remains scoped to 2 KB and receives 403 for the others. Retrieval document filtering exposes all 17 indexed, approved documents to each management role. Tokens were short-lived and kept in memory.
- `BACKEND_PORT=8001 RUN_RAG=0 bash harness/run.sh deploy --json --md`: 7 PASS / 1 FAIL / 1 WARN, unchanged from baseline. The FAIL is the existing missing optional DuckDNS updater; WARN is the existing absent Alembic version row. Gateway frontend/API/docs return HTTP 200. Report: `harness/reports/20260929-161838.{json,md}`.
- No schema migration, seed, or manual business-data changes. No paid LLM answer generation was exercised by this deployment check.
