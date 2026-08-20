# OPERATIONS.md — Vận hành MiccoRAG-v3 trên VPS `KMS`

> Runbook vận hành cho **MiccoRAG-v3**. Kèm harness kiểm chứng, thứ tự khởi động,
> thao tác thường dùng, các điểm lệch cấu hình đã biết và cảnh báo bảo mật.
> Xem thêm: [`README.md`](README.md) · [`.claude/CLAUDE.md`](.claude/CLAUDE.md) · [`AGENTS.md`](AGENTS.md)

---

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
