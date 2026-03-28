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
| 📄 **Upload tài liệu** | Hỗ trợ PDF, DOCX, TXT, MD, PPTX |
| 🧩 **Tách chunk & Embedding** | Tự động tách tài liệu, tạo vector embedding (BAAI/bge-m3) |
| 💬 **Chat thông minh** | Trả lời với ngữ cảnh tài liệu, có nguồn trích dẫn |
| 🔄 **Streaming response** | Trải nghiệm chat mượt mà, real-time |
| 🔍 **Hybrid Search** | Vector search + Reranking (Cohere rerank-multilingual-v3.0) |
| ⚡ **Fast LLM** | Gemini 2.5 Flash / Ollama — tốc độ cao, chi phí thấp |
| 🔎 **Knowledge Graph** | Trích xuất thực thể và quan hệ (NexusRAG) |
| ✅ **Phê duyệt tài liệu** | Hệ thống phê duyệt trước khi tài liệu được công khai |
| 🏢 **Phòng ban** | Gán người dùng vào phòng ban để quản lý |

### Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 + Vite)              │
│     Chat UI · Document Upload · Dashboard · Quản lý         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                      Backend (FastAPI)                        │
│  Auth · Chat · Documents · Ingest · Knowledge · Admin      │
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
miccoRAG/
│
├── micco-backend/          # 🐳 FastAPI backend
│   ├── backend/          # FastAPI source code
│   │   ├── api/          # API route handlers (v2)
│   │   ├── api_compat/   # API route handlers (legacy/compat)
│   │   ├── services/     # Business logic layer
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── core/         # Config, security, database
│   ├── docker/           # Docker compose + init scripts
│   ├── setup.sh          # Script cài đặt tự động
│   ├── run_bk.sh         # Script chạy backend
│   ├── seed_data.py      # Seed departments + user assignments
│   └── seed_users.py     # Seed default users
│
├── micco-frontend/         # 🎨 React frontend
│   ├── src/               # React source code
│   └── package.json       # Frontend dependencies
│
├── LICENSE                 # MIT License
└── README.md              # File này
```

---

## Phân quyền

Hệ thống sử dụng **Role-Based Access Control (RBAC)** với 3 vai trò:

### Vai trò

| Vai trò | Mô tả |
|---|---|
| **Admin** | Toàn quyền quản trị hệ thống |
| **Trưởng phòng** | Quản lý tài liệu và phê duyệt trong phòng ban |
| **Nhân viên** | Người dùng thông thường, có giới hạn truy cập |

### Quyền chi tiết

| Tính năng | Admin | Trưởng phòng | Nhân viên |
|---|---|---|---|
| Quản lý người dùng | ✅ Tạo/Sửa/Xóa | ❌ | ❌ |
| Quản lý phòng ban | ✅ Tạo/Sửa/Xóa | ❌ | ❌ |
| Xem lịch sử chat toàn hệ thống | ✅ | ❌ | ❌ |
| Xem thống kê hệ thống | ✅ | ❌ | ❌ |
| Phê duyệt/từ chối tài liệu | ✅ | ✅ | ❌ |
| Upload tài liệu | ✅ (auto-approved) | ✅ (auto-approved) | ✅ (cần phê duyệt) |
| Xem tài liệu trong workspace | ✅ Tất cả | ✅ Trong phòng ban | ✅ Đã phê duyệt + tài liệu của mình |
| Chat với tài liệu | ✅ | ✅ | ✅ |
| Quản lý Knowledge Base | ✅ | ✅ | ❌ |
| Quản lý Knowledge Graph | ✅ | ✅ | ❌ |

### Phòng ban mặc định

Hệ thống được seed sẵn 4 phòng ban:

| Phòng ban | Mô tả |
|---|---|
| Hành chính Nhân sự | Quản lý nhân sự và hành chính |
| Phòng Chuyên môn | Nghiệp vụ chuyên môn |
| Phòng Kỹ thuật | Hỗ trợ và triển khai kỹ thuật |
| Phòng An toàn | Quản lý an toàn và bảo mật |

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
| SQLAlchemy + asyncpg | ORM & async PostgreSQL driver |
| ChromaDB | Vector store (embeddings) |
| BAAI/bge-m3 | Embedding model (sentence-transformers) |
| Cohere rerank-multilingual-v3.0 | Reranking (high-precision multilingual retrieval) |
| Docling / Marker | Document parsing (PDF/DOCX) |
| NexusRAG | Knowledge Graph extraction |
| Google GenAI (Gemini) / Ollama | LLM providers |
| python-jose + bcrypt | JWT authentication |

### Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| Vite 7 | Build tool |
| Tailwind CSS 3 | Styling |
| Lucide React | Icon system |
| Tiptap 3 | Rich text editor |
| React Router 7 | Routing |
| Recharts 3 | Data visualization |
| React Force Graph | Knowledge graph visualization |

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
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Mở file .env và điền các API Key (GOOGLE_AI_API_KEY, COHERE_API_KEY).
```

#### Bước 3: Chạy Database Migrations

```powershell
cd backend
alembic upgrade head
```

#### Bước 4: Seed dữ liệu mặc định

```powershell
cd backend
# Seed departments + user assignments
python seed_data.py
# Seed default users (admin account)
python seed_users.py
```

#### Bước 5: Thiết lập Frontend

```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Bước 6: Chạy hệ thống

- **Backend**: `cd micco-backend/backend && uvicorn app.main:app --reload --port 8000`
- **Frontend**: `cd micco-frontend && npm run dev`
- **Truy cập**: http://localhost:5173

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
python seed_data.py   # Seed departments + user assignments
python seed_users.py  # Seed default users
```

#### Bước 5: Chạy hệ thống

- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Truy cập**: http://localhost:5173

---

## API Endpoints

### 🔐 Authentication `/api/auth`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/auth/departments` | Danh sách phòng ban | ✅ |
| POST | `/api/auth/register` | Đăng ký tài khoản mới | ✅ |
| POST | `/api/auth/login` | Đăng nhập và lấy JWT Token | ✅ |
| GET | `/api/auth/me` | Lấy thông tin người dùng hiện tại | ✅ |
| PUT | `/api/auth/me` | Cập nhật thông tin cá nhân | ✅ |

### 📚 Workspaces (Knowledge Base) `/api/workspaces`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/workspaces` | Danh sách tất cả Knowledge Base | ✅ |
| POST | `/api/workspaces` | Tạo Knowledge Base mới | Admin/Trưởng phòng |
| GET | `/api/workspaces/summary` | Danh sách rút gọn (dropdown) | ✅ |
| GET | `/api/workspaces/{id}` | Chi tiết Knowledge Base | ✅ |
| PUT | `/api/workspaces/{id}` | Cập nhật Knowledge Base | Admin/Trưởng phòng |
| DELETE | `/api/workspaces/{id}` | Xóa Knowledge Base | Admin |

### 📄 Documents `/api/documents`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/documents/workspace/{id}` | Danh sách tài liệu trong workspace | ✅ |
| POST | `/api/documents/upload/{workspace_id}` | Upload tài liệu mới | ✅ |
| GET | `/api/documents/{id}` | Chi tiết tài liệu | ✅ |
| PUT | `/api/documents/{id}` | Cập nhật tài liệu | ✅ |
| DELETE | `/api/documents/{id}` | Xóa tài liệu | ✅ |
| GET | `/api/documents/{id}/markdown` | Lấy nội dung Markdown | ✅ |
| GET | `/api/documents/{id}/images` | Danh sách hình ảnh trích xuất | ✅ |
| GET | `/api/documents/{id}/download` | Tải file gốc | ✅ |

### ✅ Phê duyệt `/api/approvals`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| GET | `/api/approvals/count` | Số tài liệu chờ phê duyệt | Admin/Trưởng phòng |
| GET | `/api/approvals/pending` | Danh sách tài liệu chờ duyệt | Admin/Trưởng phòng |
| POST | `/api/approvals/documents/{id}/approve` | Phê duyệt tài liệu | Admin/Trưởng phòng |
| POST | `/api/approvals/documents/{id}/reject` | Từ chối tài liệu | Admin/Trưởng phòng |

### 💬 Chat & RAG `/api`

| Method | Endpoint | Mô tả | Auth |
|---|---|---|---|
| POST | `/api/chat` | Chat với tài liệu (Streaming SSE) | ✅ |
| GET | `/api/rag/workspaces` | Danh sách workspace cho chat | ✅ |

### 👑 Admin `/api/admin`

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

## Biến môi trường

Trong file `micco-backend/backend/.env`:

| Biến | Mô tả | Mặc định |
|---|---|---|
| `DATABASE_URL` | Kết nối PostgreSQL | `postgresql+asyncpg://postgres:postgres@127.0.0.1:5435/nexusrag` |
| `CHROMA_HOST` | ChromaDB host | `127.0.0.1` |
| `CHROMA_PORT` | ChromaDB port | `8003` |
| `LLM_PROVIDER` | Provider: `gemini` hoặc `ollama` | `gemini` |
| `LLM_MODEL_FAST` | Model LLM sử dụng | `gemini-2.5-flash` |
| `GOOGLE_AI_API_KEY` | API Key cho Gemini | - |
| `COHERE_API_KEY` | API Key cho Cohere Reranker | - |
| `NEXUSRAG_CHUNK_MAX_TOKENS` | Kích thước chunk tối đa | `512` |
| `NEXUSRAG_KG_LANGUAGE` | Ngôn ngữ cho Knowledge Graph | `English` |

---

## 🔑 Lưu ý về Reranker

Hệ thống sử dụng **Cohere Reranker (`rerank-multilingual-v3.0`)** làm mặc định để đạt độ chính xác cao nhất cho tiếng Việt. Hãy đảm bảo bạn đã cung cấp `COHERE_API_KEY` hợp lệ trong file `.env`. Nếu không có, hệ thống sẽ sử dụng kết quả từ Vector Search truyền thống.

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

**miccoRAG v3** is an intelligent chatbot system using **RAG (Retrieval-Augmented Generation)** to answer questions based on document content. It leverages a hybrid approach combining Vector Search, Knowledge Graphs, and a robust approval workflow.

| Feature | Description |
|---|---|
| 📄 **Document Upload** | Supports PDF, DOCX, TXT, MD, PPTX |
| 🧩 **Chunking & Embedding** | Auto-split documents, generate vector embeddings (BAAI/bge-m3) |
| 💬 **Smart Chat** | Answers with document context, with citations |
| 🔄 **Streaming Response** | Smooth, real-time chat experience |
| 🔍 **Hybrid Search** | Vector search + Reranking (Cohere rerank-multilingual-v3.0) |
| ⚡ **Fast LLM** | Gemini 2.5 Flash / Ollama — fast & cost-effective |
| 🔎 **Knowledge Graph** | Entity and relationship extraction (NexusRAG) |
| ✅ **Document Approval** | Pending approval workflow before documents go public |
| 🏢 **Departments** | Assign users to departments for management |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 19 + Vite)                │
│      Chat UI · Document Upload · Dashboard · Management       │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (FastAPI)                         │
│  Auth · Chat · Documents · Ingest · Knowledge · Admin        │
└────────────┬─────────────┬──────────────┬─────────────────────┘
             │             │              │
    ┌────────▼────┐ ┌───────▼──────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │   NexusRAG  │ │  ChromaDB   │
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

## Project Structure

```
miccoRAG/
│
├── micco-backend/          # 🐳 FastAPI backend
│   ├── backend/           # FastAPI source code
│   │   ├── api/          # API route handlers (v2)
│   │   ├── api_compat/   # API route handlers (legacy/compat)
│   │   ├── services/     # Business logic layer
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── core/        # Config, security, database
│   ├── docker/          # Docker compose + init scripts
│   ├── setup.sh         # Auto-setup script
│   ├── run_bk.sh        # Run backend script
│   ├── seed_data.py     # Seed departments + user assignments
│   └── seed_users.py    # Seed default users
│
├── micco-frontend/          # 🎨 React frontend
│   ├── src/                # React source code
│   └── package.json        # Frontend dependencies
│
├── LICENSE                 # MIT License
└── README.md               # This file
```

---

## Permissions

The system uses **Role-Based Access Control (RBAC)** with 3 roles:

### Roles

| Role | Description |
|---|---|
| **Admin** | Full system administration access |
| **Trưởng phòng** (Dept. Head) | Manage and approve documents within their department |
| **Nhân viên** (Staff) | Regular user with limited access |

### Permission Matrix

| Feature | Admin | Dept. Head | Staff |
|---|---|---|---|
| Manage users | ✅ Create/Edit/Delete | ❌ | ❌ |
| Manage departments | ✅ Create/Edit/Delete | ❌ | ❌ |
| View all chat logs | ✅ | ❌ | ❌ |
| View system stats | ✅ | ❌ | ❌ |
| Approve/reject documents | ✅ | ✅ | ❌ |
| Upload documents | ✅ (auto-approved) | ✅ (auto-approved) | ✅ (needs approval) |
| View workspace documents | ✅ All | ✅ In department | ✅ Approved + own uploads |
| Chat with documents | ✅ | ✅ | ✅ |
| Manage Knowledge Base | ✅ | ✅ | ❌ |
| Manage Knowledge Graph | ✅ | ✅ | ❌ |

### Default Departments

| Department | Description |
|---|---|
| Hành chính Nhân sự | HR and Administration |
| Phòng Chuyên môn | Professional Operations |
| Phòng Kỹ thuật | Technical Support and Deployment |
| Phòng An toàn | Safety and Security Management |

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
| SQLAlchemy + asyncpg | ORM & async PostgreSQL driver |
| ChromaDB | Vector store (embeddings) |
| BAAI/bge-m3 | Embedding model (sentence-transformers) |
| Cohere rerank-multilingual-v3.0 | Reranking (high-precision multilingual retrieval) |
| Docling / Marker | Document parsing (PDF/DOCX) |
| NexusRAG | Knowledge Graph extraction |
| Google GenAI (Gemini) / Ollama | LLM providers |
| python-jose + bcrypt | JWT authentication |

### Frontend

| Technology | Purpose |
|---|---|
| React 19 | UI framework |
| Vite 7 | Build tool |
| Tailwind CSS 3 | Styling |
| Lucide React | Icon system |
| Tiptap 3 | Rich text editor |
| React Router 7 | Routing |
| Recharts 3 | Data visualization |
| React Force Graph | Knowledge graph visualization |

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
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and fill in GOOGLE_AI_API_KEY and COHERE_API_KEY.
```

#### Step 3: Run Database Migrations

```powershell
cd backend
alembic upgrade head
```

#### Step 4: Seed Default Data

```powershell
cd backend
python seed_data.py   # Seed departments + user assignments
python seed_users.py  # Seed default users
```

#### Step 5: Frontend Setup

```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Step 6: Run

- **Backend**: `cd micco-backend/backend && uvicorn app.main:app --reload --port 8000`
- **Frontend**: `cd micco-frontend && npm run dev`
- **Access**: http://localhost:5173

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
python seed_data.py   # Seed departments + user assignments
python seed_users.py  # Seed default users
```

#### Step 5: Run

- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Access**: http://localhost:5173

---

## API Endpoints

### 🔐 Authentication `/api/auth`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/auth/departments` | List departments | Public |
| POST | `/api/auth/register` | Register new account | Public |
| POST | `/api/auth/login` | Login and get JWT Token | Public |
| GET | `/api/auth/me` | Get current user info | Required |
| PUT | `/api/auth/me` | Update personal info | Required |

### 📚 Workspaces `/api/workspaces`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/workspaces` | List all Knowledge Bases | ✅ |
| POST | `/api/workspaces` | Create new Knowledge Base | Admin/Dept. Head |
| GET | `/api/workspaces/summary` | Compact list for dropdown | ✅ |
| GET | `/api/workspaces/{id}` | Get Knowledge Base details | ✅ |
| PUT | `/api/workspaces/{id}` | Update Knowledge Base | Admin/Dept. Head |
| DELETE | `/api/workspaces/{id}` | Delete Knowledge Base | Admin |

### 📄 Documents `/api/documents`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/documents/workspace/{id}` | List docs in workspace | ✅ |
| POST | `/api/documents/upload/{workspace_id}` | Upload new document | ✅ |
| GET | `/api/documents/{id}` | Get document details | ✅ |
| PUT | `/api/documents/{id}` | Update document | ✅ |
| DELETE | `/api/documents/{id}` | Delete document | ✅ |
| GET | `/api/documents/{id}/markdown` | Get Markdown content | ✅ |
| GET | `/api/documents/{id}/images` | List extracted images | ✅ |
| GET | `/api/documents/{id}/download` | Download original file | ✅ |

### ✅ Approvals `/api/approvals`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/approvals/count` | Pending approval count | Admin/Dept. Head |
| GET | `/api/approvals/pending` | List pending documents | Admin/Dept. Head |
| POST | `/api/approvals/documents/{id}/approve` | Approve document | Admin/Dept. Head |
| POST | `/api/approvals/documents/{id}/reject` | Reject document | Admin/Dept. Head |

### 💬 Chat & RAG

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/chat` | Chat with documents (Streaming SSE) | ✅ |
| GET | `/api/rag/workspaces` | List workspaces for chat | ✅ |

### 👑 Admin `/api/admin`

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

## Environment Variables

In `micco-backend/backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://postgres:postgres@127.0.0.1:5435/nexusrag` |
| `CHROMA_HOST` | ChromaDB host | `127.0.0.1` |
| `CHROMA_PORT` | ChromaDB port | `8003` |
| `LLM_PROVIDER` | Provider: `gemini` or `ollama` | `gemini` |
| `LLM_MODEL_FAST` | LLM model to use | `gemini-2.5-flash` |
| `GOOGLE_AI_API_KEY` | API Key for Gemini | - |
| `COHERE_API_KEY` | API Key for Cohere Reranker | - |
| `NEXUSRAG_CHUNK_MAX_TOKENS` | Max chunk size | `512` |
| `NEXUSRAG_KG_LANGUAGE` | Language for Knowledge Graph | `English` |

---

## 🔑 Reranker Note

The system defaults to **Cohere Reranker (`rerank-multilingual-v3.0`)** for high-precision multilingual retrieval. Please ensure a valid `COHERE_API_KEY` is configured in your `.env`. Without it, the system falls back to traditional Vector Search results.

---

## License

**MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

*[ Quay về Tiếng Việt ↑ ](#tổng-quan)*

**Made with ❤️ for RAG-powered Document Q&A · MIT License**

</div>
