<!--
 ┌─────────────────────────────────────────────────────────────────┐
 │                         🇻🇳 TIẾNG VIỆT                          │
 └─────────────────────────────────────────────────────────────────┘
-->

<div align="center">

# miccoRAG v3

### Hệ thống RAG (Retrieval-Augmented Generation) Chatbot & Document Q&A

*Hỗ trợ tải lên, xử lý và trả lời câu hỏi dựa trên tài liệu nội bộ*

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<p>
<a href="#tổng-quan">Tổng quan</a> &nbsp;|&nbsp;
<a href="#cấu-trúc-dự-án">Cấu trúc</a> &nbsp;|&nbsp;
<a href="#phân-quyền">Phân quyền</a> &nbsp;|&nbsp;
<a href="#tech-stack">Tech Stack</a> &nbsp;|&nbsp;
<a href="#hướng-dẫn-cài-đặt">Cài đặt</a> &nbsp;|&nbsp;
<a href="#api-endpoints">API</a> &nbsp;|&nbsp;
<a href="#biến-môi-trường">Env Vars</a>
</p>

*[View in English ↓](#english-version)*

</div>

---

## Tổng quan

**miccoRAG v3** là hệ thống chatbot thông minh sử dụng kỹ thuật **RAG (Retrieval-Augmented Generation)** để trả lời câu hỏi dựa trên nội dung tài liệu. Hệ thống hỗ trợ:

| Chức năng | Mô tả |
|---|---|
| 📄 **Upload tài liệu** | Hỗ trợ PDF, DOCX, TXT, MD, PPTX — kèm preview trực tiếp |
| 🧩 **Chunking & Embedding** | Tự động tách tài liệu, tạo vector embedding (Gemini Embedding API) |
| 💬 **Chat thông minh** | Trả lời với ngữ cảnh tài liệu, có nguồn trích dẫn |
| 🔄 **Streaming response** | Trải nghiệm chat mượt mà, real-time (SSE) |
| 🔍 **Hybrid Search** | Vector search + Reranking (Cohere rerank-multilingual-v3.0) |
| ⚡ **Fast LLM** | Gemini 2.5 Flash / Ollama — tốc độ cao, chi phí thấp |
| 🔎 **Knowledge Graph** | Trích xuất thực thể và quan hệ (NexusRAG) |
| ✅ **Phê duyệt tài liệu** | Hệ thống phê duyệt trước khi tài liệu được công khai |
| 🏢 **Phòng ban → Workspace** | Mỗi phòng ban có đúng 1 workspace; RBAC lọc theo department |
| 🗂️ **Bulk operations** | Chọn nhiều tài liệu, xóa hàng loạt |

### Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 + Vite 7)            │
│     Chat UI · Document Upload · Dashboard · Quản lý         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│               Backend (FastAPI — micco-backend)              │
│   v1 API: workspaces · documents · rag · config · expert   │
│   Compat API: auth · admin · approvals · chat · knowledge  │
└────────────┬─────────────┬──────────────┬───────────────────┘
             │             │              │
    ┌────────▼────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │   NexusRAG │ │  ChromaDB   │
    │ + asyncpg   │ │ Knowledge   │ │ Vector Store│
    │ (metadata)  │ │   Graph     │ │(embeddings) │
    └─────────────┘ └─────────────┘ └──────────────┘
             │
    ┌────────▼────────┐
    │  LLM Providers  │
    │Gemini / Ollama  │
    └─────────────────┘
```

---

## Cấu trúc dự án

```
miccoRAG-v3/
│
├── micco-backend/              # FastAPI backend (NexusRAG)
│   ├── backend/
│   │   ├── api/              # v2 API routers (workspaces, documents, rag, config, expert)
│   │   ├── api_compat/       # Legacy compat (auth, admin, chat, docs, approvals, knowledge)
│   │   ├── core/             # config, database, security, deps, exceptions, rls
│   │   ├── models/           # SQLAlchemy models (9 models)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   └── services/         # Business logic + llm package + document_parser package
│   ├── alembic/versions/     # 4 migration files
│   ├── docker-compose.*.yml  # PostgreSQL 15435 + ChromaDB 8003 + Nginx
│   ├── seed_data.py          # Seed 6 departments + user assignments
│   └── seed_users.py         # Seed admin + 3 users
│
├── micco-frontend/            # React 19 + Vite frontend
│   ├── src/
│   │   ├── pages/            # 13 page components
│   │   ├── components/       # 8 component categories
│   │   ├── layouts/          # DashboardLayout with sidebar nav
│   │   ├── context/          # AuthContext, ThemeContext
│   │   └── utils/api.js      # Centralized API service layer
│   └── tailwind.config.js
│
├── micco-server/              # Standalone legacy backend
│
├── .claude/                  # Claude Code project memory
│   ├── CLAUDE.md             # Project memory & conventions
│   ├── agents/               # Agent definitions
│   ├── commands/             # Claude Code skills
│   ├── rules/                # Coding rules (frontend, api-design, llm, rag, testing...)
│   └── skills/               # Claude Code skill definitions
│
├── LICENSE
└── README.md
```

---

## Phân quyền

Hệ thống sử dụng **Role-Based Access Control (RBAC)** với 3 vai trò:

| Vai trò | Mô tả |
|---|---|
| **Admin** | Toàn quyền quản trị hệ thống |
| **Trưởng phòng** | Quản lý tài liệu và phê duyệt trong phòng ban |
| **Nhân viên** | Người dùng thông thường, upload cần phê duyệt |

### Quyền chi tiết

| Tính năng | Admin | Trưởng phòng | Nhân viên |
|---|---|---|---|
| Quản lý người dùng | ✅ Tạo/Sửa/Xóa | ❌ | ❌ |
| Quản lý phòng ban | ✅ Tạo/Sửa/Xóa | ❌ | ❌ |
| Xem lịch sử chat toàn hệ thống | ✅ | ❌ | ❌ |
| Xem thống kê hệ thống | ✅ | ❌ | ❌ |
| Phê duyệt/từ chối tài liệu | ✅ | ✅ | ❌ |
| Upload tài liệu | ✅ (auto-approved) | ✅ (auto-approved) | ✅ (cần phê duyệt) |
| Xem workspace | ✅ Tất cả | ✅ Phòng ban mình | ✅ Phòng ban mình |
| Chat với tài liệu | ✅ | ✅ | ✅ |
| Quản lý Knowledge Base | ✅ | ✅ | ❌ |
| Quản lý Knowledge Graph | ✅ | ✅ | ❌ |

### Phòng ban mặc định (6 phòng ban)

| Phòng ban | Mô tả |
|---|---|
| Ban Giám đốc | Ban lãnh đạo công ty |
| Kinh doanh | Phòng Kinh doanh - Marketing |
| Kế toán | Phòng Kế toán - Tài chính |
| Kỹ thuật | Phòng Kỹ thuật - Công nghệ |
| Nhân sự | Phòng Nhân sự |
| Pháp chế | Phòng Pháp chế - Hợp đồng |

> Mỗi phòng ban được tự động gán **1 workspace (Knowledge Base)** duy nhất khi seed.

### Quy trình phê duyệt tài liệu

```
Nhân viên upload → [pending] → Trưởng phòng/Admin duyệt → [approved] → Công khai cho workspace
                                              ↓
                                    Trưởng phòng/Admin từ chối → [rejected] → Ghi chú lý do
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| FastAPI | Async REST API framework |
| SQLAlchemy 2.0+ (async) + asyncpg | ORM & async PostgreSQL driver |
| ChromaDB | Vector store (embeddings) |
| **Gemini Embedding API** / sentence-transformers | Embedding generation |
| Cohere rerank-multilingual-v3.0 | Reranking (high-precision multilingual retrieval) |
| Docling 2.0+ / Marker | Document parsing (PDF/DOCX) |
| NexusRAG | Knowledge Graph extraction |
| Google GenAI (Gemini) / Ollama | LLM providers |
| python-jose + bcrypt | JWT authentication |

### Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| Vite 7 | Build tool |
| Tailwind CSS 3 + @tailwindcss/typography | Styling |
| Lucide React | Icon system |
| Tiptap 3 | Rich text editor |
| React Router 7 | Routing |
| Recharts 3 | Data visualization |
| React Force Graph 2D | Knowledge graph visualization |
| docx-preview | DOCX file preview |

---

## Hướng dẫn cài đặt

### Yêu cầu tiên quyết

| Yêu cầu | Phiên bản |
|---|---|
| Docker Desktop (Windows) / Docker Engine (Ubuntu) | Latest |
| Node.js | v18+ |
| Python | 3.10+ |
| pnpm | Latest (`npm install -g pnpm`) |

---

### 🪟 Cách 1: Thiết lập trên WINDOWS

#### Bước 1: Khởi động database services (PostgreSQL + ChromaDB)

```powershell
cd micco-backend
docker-compose -f docker-compose.services.yml up -d
```

#### Bước 2: Thiết lập Backend

```powershell
cd micco-backend/backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Mở file .env và điền các API Key (GOOGLE_AI_API_KEY, COHERE_API_KEY).
```

#### Bước 3: Chạy Database Migrations (tự động khi khởi động)

```powershell
cd micco-backend/backend
alembic upgrade head
```

#### Bước 4: Seed dữ liệu mặc định

```powershell
cd micco-backend/backend
python seed_data.py   # Seed 6 departments + user assignments
python seed_users.py  # Seed admin + 3 users
```

#### Bước 5: Thiết lập Frontend

```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Bước 6: Chạy hệ thống

- **Backend**: `cd micco-backend/backend && uvicorn app.main:app --reload --port 8001`
- **Frontend**: `cd micco-frontend && npm run dev`
- **Truy cập**: http://localhost:5174

---

### 🐧 Cách 2: Thiết lập trên UBUNTU / LINUX

#### Bước 1: Chạy Script thiết lập tự động

```bash
cd micco-backend
chmod +x setup.sh run_bk.sh
./setup.sh
```

*Script này tự động: Tạo venv, cài thư viện Python, khởi động Docker Services, và cài npm packages cho frontend.*

#### Bước 2: Cấu hình

Sửa file `.env` trong `micco-backend/backend/` và điền các API Key cần thiết.

#### Bước 3: Chạy Database Migrations

```bash
cd micco-backend/backend
alembic upgrade head
```

#### Bước 4: Seed dữ liệu mặc định

```bash
cd micco-backend/backend
python seed_data.py   # Seed 6 departments + user assignments
python seed_users.py  # Seed admin + 3 users
```

#### Bước 5: Chạy hệ thống

- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Truy cập**: http://localhost:5174

---

### 🐳 Docker (Production)

```bash
# Start all services with Nginx
cd micco-backend
docker compose -f docker-compose.nginx.yml up -d

# Full production stack
docker compose up -d
```

---

## API Endpoints

### Dual-backend architecture

| Backend | Prefix | Purpose |
|---|---|---|
| **micco-backend** (NexusRAG) | `/api/v1/*` | Workspaces, Documents, RAG, Config, Expert |
| **micco-server** (Legacy compat) | `/api/*` | Auth, Admin, Approvals, Chat, Knowledge |

Frontend sử dụng cả hai backend: `ragFetch()` → legacy API, `ragFetchV2()` → v1 API.

### 🔐 Authentication `/api/auth`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/auth/departments` | Danh sách phòng ban | ✅ |
| POST | `/api/auth/register` | Đăng ký tài khoản mới | ✅ |
| POST | `/api/auth/login` | Đăng nhập và lấy JWT Token | ✅ |
| GET | `/api/auth/me` | Lấy thông tin người dùng hiện tại | ✅ |
| PUT | `/api/auth/me` | Cập nhật thông tin cá nhân | ✅ |

### 📚 Workspaces `/api/v1/workspaces` (v2)

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/v1/workspaces` | Danh sách workspace (Admin: tất cả; User: phòng mình) | ✅ |
| POST | `/api/v1/workspaces` | Tạo workspace mới | Admin/Trưởng phòng |
| GET | `/api/v1/workspaces/summary` | Danh sách rút gọn (dropdown) | ✅ |
| GET | `/api/v1/workspaces/{id}` | Chi tiết workspace | ✅ |
| PUT | `/api/v1/workspaces/{id}` | Cập nhật workspace | Admin/Trưởng phòng |
| DELETE | `/api/v1/workspaces/{id}` | Xóa workspace | Admin |

### 📄 Documents `/api/v1/documents` (v2)

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/v1/documents/workspace/{id}` | Danh sách tài liệu trong workspace | ✅ |
| POST | `/api/v1/documents/upload/{workspace_id}` | Upload tài liệu mới | ✅ |
| GET | `/api/v1/documents/{id}` | Chi tiết tài liệu | ✅ |
| PUT | `/api/v1/documents/{id}` | Cập nhật tài liệu | ✅ |
| DELETE | `/api/v1/documents/{id}` | Xóa tài liệu | ✅ |
| GET | `/api/v1/documents/{id}/markdown` | Lấy nội dung Markdown | ✅ |
| GET | `/api/v1/documents/{id}/images` | Danh sách hình ảnh trích xuất | ✅ |
| GET | `/api/v1/documents/{id}/download` | Tải file gốc | ✅ |
| GET | `/api/v1/documents/{id}/preview` | Preview text (DOCX/TXT/MD) | ✅ |

### 💬 RAG Chat `/api/v1/rag`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| POST | `/api/v1/rag/chat/{workspace_id}/stream` | Chat streaming (SSE) | ✅ |
| POST | `/api/v1/rag/chat/{workspace_id}` | Chat non-streaming | ✅ |
| GET | `/api/v1/rag/chat/{workspace_id}/history` | Lịch sử chat | ✅ |
| DELETE | `/api/v1/rag/chat/{workspace_id}/history` | Xóa lịch sử chat | ✅ |
| POST | `/api/v1/rag/query/{workspace_id}` | RAG query (retrieve chunks) | ✅ |
| POST | `/api/v1/rag/process/{doc_id}` | Process single document | ✅ |
| POST | `/api/v1/rag/process-batch` | Batch process documents | ✅ |
| GET | `/api/v1/rag/stats/{workspace_id}` | RAG statistics | ✅ |
| GET | `/api/v1/rag/graph/{workspace_id}` | Knowledge graph data | ✅ |

### ✅ Phê duyệt `/api/approvals` (compat)

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/approvals/count` | Số tài liệu chờ phê duyệt | Admin/Trưởng phòng |
| GET | `/api/approvals/pending` | Danh sách tài liệu chờ duyệt | Admin/Trưởng phòng |
| POST | `/api/approvals/documents/{id}/approve` | Phê duyệt tài liệu | Admin/Trưởng phòng |
| POST | `/api/approvals/documents/{id}/reject` | Từ chối tài liệu | Admin/Trưởng phòng |

### 👑 Admin `/api/admin` (compat)

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/admin/stats` | Thống kê hệ thống | Admin |
| GET | `/api/admin/departments` | Danh sách phòng ban + user count | Admin |
| POST | `/api/admin/departments` | Tạo phòng ban | Admin |
| PUT | `/api/admin/departments/{id}` | Cập nhật phòng ban | Admin |
| DELETE | `/api/admin/departments/{id}` | Xóa phòng ban | Admin |
| GET | `/api/admin/users` | Danh sách người dùng (phân trang) | Admin |
| POST | `/api/admin/users` | Tạo người dùng | Admin |
| PUT | `/api/admin/users/{id}` | Cập nhật người dùng | Admin |
| DELETE | `/api/admin/users/{id}` | Xóa người dùng | Admin |
| GET | `/api/admin/chat-logs` | Lịch sử chat toàn hệ thống | Admin |

---

## 🧪 Kiểm thử & Harness

Dự án có **hệ harness đa-thành-phần** dưới `harness/` — kiểm chứng toàn stack theo từng
thành phần: **smoke · be · fe · qa · test · deploy · eval · bench**. Mọi component in
`TỔNG: N PASS / M FAIL / K WARN`, **exit 0 khi không FAIL**, và **chỉ đụng container
`nexusrag-*`/`micco-*`** (an toàn trên VPS dùng chung).

```bash
# Chạy nhiều component (mặc định 'all' = smoke+be+fe+test+deploy — miễn phí)
bash harness/run.sh all --json
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh all'   # từ xa

# Một component
bash harness/run.sh smoke      # hạ tầng/health (tương thích: harness_smoke.sh vẫn chạy)
bash harness/run.sh qa         # cổng chất lượng → 🟢 GO / 🔴 NO-GO

# Các tầng TỐN PHÍ (gọi Gemini) — bật cờ:
RUN_EVAL=1  bash harness/run.sh eval     # chất lượng RAG (retrieval/keyword/citation/pass@1)
RUN_BENCH=1 bash harness/run.sh bench    # latency p50/p95 theo mode
RUN_E2E=1   bash harness/run.sh fe       # Playwright e2e
bash harness/run.sh full --paid          # tất cả, kể cả eval+bench
```

| Component | Kiểm | | Component | Kiểm |
|---|---|---|---|---|
| **smoke** | Docker/DB/API/nginx/FE health | | **deploy** | services/migrations/seed/routing (read-only) |
| **be** | ruff + pytest unit + coverage (+integration) | | **test** | mọi pytest suite |
| **fe** | eslint + `vite build` + e2e | | **eval** | chất lượng RAG trên golden set |
| **qa** | gate GO/NO-GO | | **bench** | latency per search mode |

Mỗi lĩnh vực có một **subagent chuyên trách** trong `.claude/agents/` — `backend`, `frontend`,
`qa`, `deploy`, `test`, `eval`, `bench` (+ `harness-orchestrator`). Đây là agent **làm việc đầy
đủ, tự-động-định-tuyến**: khi có task thuộc lĩnh vực nào thì agent đó tự implement/sửa + test +
verify bằng harness tương ứng. Kèm lệnh `/harness [component]`. Artifact `--json`/`--md` ghi vào
`harness/reports/`. Chi tiết vận hành: [`OPERATIONS.md`](OPERATIONS.md).

> Các dòng `⚠️ WARN` là cảnh báo (vd. lệch cấu hình nginx, dep còn thiếu), không làm
> harness thất bại.

---

## 🚀 Vận hành trên VPS `KMS`

Bản chạy production đặt tại VPS `KMS` — `ssh KMS`, thư mục `/home/kms/MiccoRAG-v3`.

| Thành phần | Cổng | Ghi chú |
|---|---|---|
| Backend dev (`run_bk.sh`) | **8001** | `uvicorn --reload` |
| Backend prod | 8000 | `uvicorn --workers 2` |
| Frontend (Vite) | 5174 | `npm run dev` |
| PostgreSQL | **15435** → 5432 | container `nexusrag-postgres`, db `nexusrag` |
| ChromaDB | 8003 | container `nexusrag-chromadb` |
| Nginx gateway | 8888 | container `micco-nginx-gw` (`network_mode: host`) |

> ⚠️ `KMS` là **VPS dùng chung** (nhiều dự án khác). Chỉ thao tác trên các container
> `nexusrag-*` / `micco-*`. Thứ tự khởi động, xử lý sự cố, các điểm lệch cấu hình đã
> biết và cảnh báo bảo mật: xem **[`OPERATIONS.md`](OPERATIONS.md)**.

---

## Biến môi trường

Trong file `micco-backend/backend/.env`:

| Biến | Mô tả | Mặc định |
|---|---|---|
| `DATABASE_URL` | Kết nối PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:15435/nexusrag` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `CHROMA_PORT` | ChromaDB port | `8003` |
| `LLM_PROVIDER` | Provider: `gemini` hoặc `ollama` | `gemini` |
| `LLM_MODEL_FAST` | Model LLM sử dụng | `gemini-2.5-flash` |
| `GOOGLE_AI_API_KEY` | API Key cho Gemini | - |
| `OLLAMA_HOST` | Ollama host | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model | `gemma3:12b` |
| `KG_EMBEDDING_PROVIDER` | Embedding provider | `gemini` |
| `COHERE_API_KEY` | API Key cho Cohere Reranker | - |
| `JWT_SECRET_KEY` | Secret cho JWT | - |
| `NEXUSRAG_EMBEDDING_MODEL` | Model embedding | `gemini` |
| `NEXUSRAG_CHUNK_MAX_TOKENS` | Kích thước chunk tối đa | `512` |
| `COMPAT_ENABLE_LEGACY_ROUTES` | Bật legacy API routes | `true` |

---

## 🔑 Lưu ý

### Embedding
Hệ thống sử dụng **Gemini Embedding API** làm embedding provider mặc định. Có thể switch sang `sentence_transformers` (local, không cần API key) bằng cách cấu hình `KG_EMBEDDING_PROVIDER=sentence_transformers`.

### Reranker
Hệ thống sử dụng **Cohere Reranker (`rerank-multilingual-v3.0`)** làm mặc định để đạt độ chính xác cao nhất cho tiếng Việt. Không có `COHERE_API_KEY` → fallback sang Vector Search truyền thống.

---

## License

**MIT License** — xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

<!--
 ┌─────────────────────────────────────────────────────────────────┐
 │                          🇺🇸 ENGLISH                             │
 └─────────────────────────────────────────────────────────────────┘
-->

<div id="english-version"></div>

---

<div align="center">

# miccoRAG v3

### RAG (Retrieval-Augmented Generation) Chatbot & Document Q&A System

*Upload, process, and answer questions based on internal documents*

[![MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<p>
<a href="#overview">Overview</a> &nbsp;|&nbsp;
<a href="#project-structure">Structure</a> &nbsp;|&nbsp;
<a href="#permissions">Permissions</a> &nbsp;|&nbsp;
<a href="#tech-stack-1">Tech Stack</a> &nbsp;|&nbsp;
<a href="#installation">Installation</a> &nbsp;|&nbsp;
<a href="#api-endpoints-1">API</a> &nbsp;|&nbsp;
<a href="#environment-variables">Env Vars</a>
</p>

</div>

---

## Overview

**miccoRAG v3** is an intelligent chatbot system using **RAG (Retrieval-Augmented Generation)** to answer questions based on document content. Key updates in this version:

| Feature | Description |
|---|---|
| 📄 **Document Upload** | Supports PDF, DOCX, TXT, MD, PPTX — with native DOCX preview |
| 🧩 **Chunking & Embedding** | Auto-split documents, **Gemini Embedding API** (configurable) |
| 💬 **Smart Chat** | Answers with document context, with citations, **SSE streaming** |
| 🔍 **Hybrid Search** | Vector search + **Cohere Reranker** for high-precision multilingual retrieval |
| ⚡ **Fast LLM** | Gemini 2.5 Flash / Ollama — fast & cost-effective |
| 🔎 **Knowledge Graph** | Entity and relationship extraction (**NexusRAG**) |
| ✅ **Document Approval** | Pending approval workflow before documents go public |
| 🏢 **Dept → Workspace 1:1** | Each department owns exactly one workspace; RBAC filtering |
| 🗂️ **Bulk Operations** | Multi-select and bulk delete documents |
| 🔄 **Approval Badge** | Real-time badge updates via polling (AuthContext) |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (React 19 + Vite 7)                │
│      Chat UI · Document Upload · Dashboard · Management       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                Backend (FastAPI — micco-backend)             │
│   v1 API: workspaces · documents · rag · config · expert    │
│   Compat API: auth · admin · approvals · chat · knowledge    │
└────────────┬─────────────┬──────────────┬────────────────────┘
             │             │              │
    ┌────────▼────┐ ┌──────▼───────┐ ┌─────▼───────┐
    │ PostgreSQL  │ │   NexusRAG  │ │  ChromaDB   │
    │ + asyncpg   │ │ Knowledge   │ │Vector Store │
    │ (metadata)  │ │   Graph     │ │(embeddings) │
    └─────────────┘ └─────────────┘ └─────────────┘
             │
    ┌────────▼────────┐
    │  LLM Providers  │
    │Gemini / Ollama  │
    └─────────────────┘
```

---

## Project Structure

```
miccoRAG-v3/
│
├── micco-backend/              # FastAPI backend (NexusRAG)
│   ├── backend/
│   │   ├── api/              # v2 API routers (workspaces, documents, rag, config, expert)
│   │   ├── api_compat/       # Legacy compat (auth, admin, chat, docs, approvals, knowledge)
│   │   ├── core/             # config, database, security, deps, exceptions, rls
│   │   ├── models/           # SQLAlchemy models (9 models)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   └── services/         # Business logic + llm package + document_parser package
│   ├── alembic/versions/     # 4 migration files
│   ├── docker-compose.*.yml   # PostgreSQL 15435 + ChromaDB 8003 + Nginx
│   ├── seed_data.py          # Seed 6 departments + user assignments
│   └── seed_users.py         # Seed admin + 3 users
│
├── micco-frontend/              # React 19 + Vite frontend
│   ├── src/
│   │   ├── pages/            # 13 page components
│   │   ├── components/       # 8 component categories
│   │   ├── layouts/           # DashboardLayout with sidebar nav
│   │   ├── context/          # AuthContext, ThemeContext
│   │   └── utils/api.js       # Centralized API service layer
│   └── tailwind.config.js
│
├── micco-server/                # Standalone legacy backend
│
├── .claude/                    # Claude Code project memory
│   ├── CLAUDE.md               # Project memory & conventions
│   ├── agents/                 # Agent definitions (backend, frontend, QA)
│   ├── commands/               # Claude Code skills
│   ├── rules/                  # Coding rules (frontend, api-design, llm, rag, testing...)
│   └── skills/                 # Claude Code skill definitions
│
├── LICENSE
└── README.md
```

---

## Permissions

The system uses **Role-Based Access Control (RBAC)** with 3 roles:

| Role | Description |
|---|---|
| **Admin** | Full system administration access |
| **Trưởng phòng** (Dept. Head) | Manage and approve documents within their department |
| **Nhân viên** (Staff) | Regular user; uploads require approval |

### Permission Matrix

| Feature | Admin | Dept. Head | Staff |
|---|---|---|---|
| Manage users | ✅ Create/Edit/Delete | ❌ | ❌ |
| Manage departments | ✅ Create/Edit/Delete | ❌ | ❌ |
| View all chat logs | ✅ | ❌ | ❌ |
| View system stats | ✅ | ❌ | ❌ |
| Approve/reject documents | ✅ | ✅ | ❌ |
| Upload documents | ✅ (auto-approved) | ✅ (auto-approved) | ✅ (needs approval) |
| View workspaces | ✅ All | ✅ Own department | ✅ Own department |
| Chat with documents | ✅ | ✅ | ✅ |
| Manage Knowledge Base | ✅ | ✅ | ❌ |
| Manage Knowledge Graph | ✅ | ✅ | ❌ |

### Default Departments (6 departments)

| Department | Description |
|---|---|
| Ban Giám đốc | Company leadership |
| Kinh doanh | Sales & Marketing |
| Kế toán | Accounting & Finance |
| Kỹ thuật | Technical & Engineering |
| Nhân sự | Human Resources |
| Pháp chế | Legal & Contracts |

> Each department is automatically assigned **1 workspace (Knowledge Base)** upon seeding.

### Document Approval Workflow

```
Staff uploads → [pending] → Dept. Head/Admin approves → [approved] → Public in workspace
                                                ↓
                              Dept. Head/Admin rejects → [rejected] → Note attached
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|---|---|
| FastAPI | Async REST API framework |
| SQLAlchemy 2.0+ (async) + asyncpg | ORM & async PostgreSQL driver |
| ChromaDB | Vector store (embeddings) |
| **Gemini Embedding API** / sentence-transformers | Embedding generation |
| Cohere rerank-multilingual-v3.0 | Reranking (high-precision multilingual retrieval) |
| Docling 2.0+ / Marker | Document parsing (PDF/DOCX) |
| NexusRAG | Knowledge Graph extraction |
| Google GenAI (Gemini) / Ollama | LLM providers |
| python-jose + bcrypt | JWT authentication |

### Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| Vite 7 | Build tool |
| Tailwind CSS 3 + @tailwindcss/typography | Styling |
| Lucide React | Icon system |
| Tiptap 3 | Rich text editor |
| React Router 7 | Routing |
| Recharts 3 | Data visualization |
| React Force Graph 2D | Knowledge graph visualization |
| docx-preview | DOCX file preview (client-side) |

---

## Installation

### Prerequisites

| Requirement | Version |
|---|---|
| Docker Desktop (Windows) / Docker Engine (Ubuntu) | Latest |
| Node.js | v18+ |
| Python | 3.10+ |
| pnpm | Latest (`npm install -g pnpm`) |

---

### 🪟 Option 1: WINDOWS Setup

#### Step 1: Start Database Services (PostgreSQL + ChromaDB)

```powershell
cd micco-backend
docker-compose -f docker-compose.services.yml up -d
```

#### Step 2: Backend Setup

```powershell
cd micco-backend/backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and fill in GOOGLE_AI_API_KEY and COHERE_API_KEY.
```

#### Step 3: Run Database Migrations

```powershell
cd micco-backend/backend
alembic upgrade head
```

#### Step 4: Seed Default Data

```powershell
cd micco-backend/backend
python seed_data.py   # Seed 6 departments + user assignments
python seed_users.py  # Seed admin + 3 users
```

#### Step 5: Frontend Setup

```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Step 6: Run

- **Backend**: `cd micco-backend/backend && uvicorn app.main:app --reload --port 8001`
- **Frontend**: `cd micco-frontend && npm run dev`
- **Access**: http://localhost:5174

---

### 🐧 Option 2: UBUNTU / LINUX Setup

#### Step 1: Run Automation Script

```bash
cd micco-backend
chmod +x setup.sh run_bk.sh
./setup.sh
```

*This script automatically: Creates venv, installs Python packages, starts Docker Services, and installs frontend npm packages.*

#### Step 2: Configuration

Edit `micco-backend/backend/.env` with your API keys.

#### Step 3: Run Database Migrations

```bash
cd micco-backend/backend
alembic upgrade head
```

#### Step 4: Seed Default Data

```bash
cd micco-backend/backend
python seed_data.py   # Seed 6 departments + user assignments
python seed_users.py  # Seed admin + 3 users
```

#### Step 5: Run

- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Access**: http://localhost:5174

---

### 🐳 Docker (Production)

```bash
# Start all services with Nginx
cd micco-backend
docker compose -f docker-compose.nginx.yml up -d

# Full production stack
docker compose up -d
```

---

## API Endpoints

### Dual-backend architecture

| Backend | Prefix | Purpose |
|---|---|---|
| **micco-backend** (NexusRAG) | `/api/v1/*` | Workspaces, Documents, RAG, Config, Expert |
| **micco-server** (Legacy compat) | `/api/*` | Auth, Admin, Approvals, Chat, Knowledge |

Frontend uses both: `ragFetch()` → legacy API, `ragFetchV2()` → v1 API.

### 🔐 Authentication `/api/auth`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/auth/departments` | List departments | ✅ |
| POST | `/api/auth/register` | Register new account | ✅ |
| POST | `/api/auth/login` | Login and get JWT Token | ✅ |
| GET | `/api/auth/me` | Get current user info | ✅ |
| PUT | `/api/auth/me` | Update personal info | ✅ |

### 📚 Workspaces `/api/v1/workspaces` (v2)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/workspaces` | List workspaces (Admin: all; User: own dept) | ✅ |
| POST | `/api/v1/workspaces` | Create new workspace | Admin/Dept. Head |
| GET | `/api/v1/workspaces/summary` | Compact list for dropdown | ✅ |
| GET | `/api/v1/workspaces/{id}` | Get workspace details | ✅ |
| PUT | `/api/v1/workspaces/{id}` | Update workspace | Admin/Dept. Head |
| DELETE | `/api/v1/workspaces/{id}` | Delete workspace | Admin |

### 📄 Documents `/api/v1/documents` (v2)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/documents/workspace/{id}` | List docs in workspace | ✅ |
| POST | `/api/v1/documents/upload/{workspace_id}` | Upload new document | ✅ |
| GET | `/api/v1/documents/{id}` | Get document details | ✅ |
| PUT | `/api/v1/documents/{id}` | Update document | ✅ |
| DELETE | `/api/v1/documents/{id}` | Delete document | ✅ |
| GET | `/api/v1/documents/{id}/markdown` | Get Markdown content | ✅ |
| GET | `/api/v1/documents/{id}/images` | List extracted images | ✅ |
| GET | `/api/v1/documents/{id}/download` | Download original file | ✅ |
| GET | `/api/v1/documents/{id}/preview` | Preview text (DOCX/TXT/MD) | ✅ |

### 💬 RAG Chat `/api/v1/rag`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/rag/chat/{workspace_id}/stream` | Chat streaming (SSE) | ✅ |
| POST | `/api/v1/rag/chat/{workspace_id}` | Chat non-streaming | ✅ |
| GET | `/api/v1/rag/chat/{workspace_id}/history` | Get chat history | ✅ |
| DELETE | `/api/v1/rag/chat/{workspace_id}/history` | Clear chat history | ✅ |
| POST | `/api/v1/rag/query/{workspace_id}` | RAG query (retrieve chunks) | ✅ |
| POST | `/api/v1/rag/process/{doc_id}` | Process single document | ✅ |
| POST | `/api/v1/rag/process-batch` | Batch process documents | ✅ |
| GET | `/api/v1/rag/stats/{workspace_id}` | RAG statistics | ✅ |
| GET | `/api/v1/rag/graph/{workspace_id}` | Knowledge graph data | ✅ |

### ✅ Approvals `/api/approvals` (compat)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/approvals/count` | Pending approval count | Admin/Dept. Head |
| GET | `/api/approvals/pending` | List pending documents | Admin/Dept. Head |
| POST | `/api/approvals/documents/{id}/approve` | Approve document | Admin/Dept. Head |
| POST | `/api/approvals/documents/{id}/reject` | Reject document | Admin/Dept. Head |

### 👑 Admin `/api/admin` (compat)

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/admin/stats` | System statistics | Admin |
| GET | `/api/admin/departments` | List departments + user count | Admin |
| POST | `/api/admin/departments` | Create department | Admin |
| PUT | `/api/admin/departments/{id}` | Update department | Admin |
| DELETE | `/api/admin/departments/{id}` | Delete department | Admin |
| GET | `/api/admin/users` | List users (paginated) | Admin |
| POST | `/api/admin/users` | Create user | Admin |
| PUT | `/api/admin/users/{id}` | Update user | Admin |
| DELETE | `/api/admin/users/{id}` | Delete user | Admin |
| GET | `/api/admin/chat-logs` | All chat logs (system-wide) | Admin |

---

## 🧪 Testing & Harness

The repo ships **`harness_smoke.sh`** — a read-only *smoke + health* harness (bash)
that verifies the whole stack is up and the RAG pipeline works. Safe to run on the
shared host.

```bash
bash harness_smoke.sh                 # local
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness_smoke.sh'   # remote
RUN_RAG=1 bash harness_smoke.sh       # also hit a real RAG /query (uses Gemini API)
BACKEND_PORT=8001 bash harness_smoke.sh
```

It checks Docker services, PostgreSQL (`pg_isready` + core tables), ChromaDB
heartbeat, backend `/health` + `/ready`, `/api/v1` surface, Swagger, nginx gateway
and frontend, printing `TỔNG: N PASS / M FAIL / K WARN` and **exiting 0 when no FAIL**.

## 🚀 Running on VPS `KMS`

Production lives on VPS `KMS` (`ssh KMS`, `/home/kms/MiccoRAG-v3`). Ports: backend dev
**8001** / prod 8000, frontend 5174, PostgreSQL **15435**, ChromaDB 8003, nginx gateway
8888. `KMS` is a **shared VPS** — only touch `nexusrag-*` / `micco-*` containers. See
**[`OPERATIONS.md`](OPERATIONS.md)** for startup order, troubleshooting, known config
drift and security notes.

---

## Environment Variables

In `micco-backend/backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://postgres:postgres@localhost:15435/nexusrag` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `CHROMA_PORT` | ChromaDB port | `8003` |
| `LLM_PROVIDER` | Provider: `gemini` or `ollama` | `gemini` |
| `LLM_MODEL_FAST` | LLM model to use | `gemini-2.5-flash` |
| `GOOGLE_AI_API_KEY` | API Key for Gemini | - |
| `OLLAMA_HOST` | Ollama host | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model | `gemma3:12b` |
| `KG_EMBEDDING_PROVIDER` | Embedding provider | `gemini` |
| `COHERE_API_KEY` | API Key for Cohere Reranker | - |
| `JWT_SECRET_KEY` | JWT secret | - |
| `NEXUSRAG_EMBEDDING_MODEL` | Embedding model | `gemini` |
| `NEXUSRAG_CHUNK_MAX_TOKENS` | Max chunk size | `512` |
| `COMPAT_ENABLE_LEGACY_ROUTES` | Enable legacy API routes | `true` |

---

## 🔑 Notes

### Embedding
The system uses **Gemini Embedding API** as the default embedding provider. Switch to `sentence_transformers` (local, no API key) by setting `KG_EMBEDDING_PROVIDER=sentence_transformers`.

### Reranker
The system defaults to **Cohere Reranker (`rerank-multilingual-v3.0`)** for high-precision multilingual retrieval. Without `COHERE_API_KEY`, it falls back to traditional Vector Search.

---

## License

**MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

*[ Quay về Tiếng Việt ↑ ](#tổng-quan)*

**Made with ❤️ for RAG-powered Document Q&A · MIT License**

</div>
