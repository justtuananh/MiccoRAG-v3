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
| 📄 **Upload tài liệu** | Hỗ trợ PDF, DOCX, TXT |
| 🧩 **Tách chunk & Embedding** | Tự động tách tài liệu, tạo vector embedding (BAAI/bge-m3) |
| 💬 **Chat thông minh** | Trả lời với ngữ cảnh tài liệu, có nguồn trích dẫn |
| 🔄 **Streaming response** | Trải nghiệm chat mượt mà, real-time |
| 🔍 **Hybrid Search** | Vector search + Reranking (Cohere rerank-multilingual-v3.0) |
| ⚡ **Fast LLM** | Gemini 2.5 Flash / Ollama — tốc độ cao, chi phí thấp |

### Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 + Vite)            │
│         Chat UI · Document Upload · Dashboard               │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  Auth · Chat · Documents · Ingest · Knowledge · Admin      │
└────────────┬─────────────┬──────────────┬───────────────────┘
             │             │              │
    ┌────────▼────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │ PostgreSQL   │ │  LightRAG  │ │  ChromaDB   │
    │ + asyncpg    │ │ Knowledge  │ │ Vector Store│
    │ (metadata)   │ │   Graph    │ │(embeddings) │
    └─────────────┘ └────────────┘ └──────────────┘
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
│   ├── backend/            # FastAPI source code
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic layer
│   │   ├── models/        # SQLAlchemy models
│   │   └── ...
│   ├── docker/            # Docker compose files (Postgres, Chroma)
│   ├── setup.sh           # Script cài đặt tự động (Ubuntu/Linux)
│   ├── run_bk.sh          # Script chạy backend (Ubuntu/Linux)
│   └── run_bk.bat         # Script chạy backend (Windows)
│
├── micco-frontend/         # 🎨 React frontend
│   ├── src/               # React source code
│   └── package.json       # Frontend dependencies
│
├── LICENSE                 # MIT License
└── README.md              # File này
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
| Docling | Document parsing (PDF/DOCX) |
| LightRAG | Knowledge Graph extraction |
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

#### Bước 3: Thiết lập Frontend

```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Bước 4: Chạy hệ thống

- **Backend**: Mở Terminal mới, `cd micco-backend\backend`, chạy `.\start_server.bat` (hoặc `.\run_bk.bat` ở thư mục ngoài).
- **Frontend**: Mở Terminal mới, `cd micco-frontend`, chạy `npm run dev`.
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

#### Bước 3: Chạy hệ thống

- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Truy cập**: http://localhost:5173

---

## API Endpoints

### 🔐 Authentication
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/auth/login` | Đăng nhập và lấy JWT Token |
| GET | `/api/auth/me` | Lấy thông tin người dùng hiện tại |

### 💬 Chat & RAG
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/chat` | Chat với tài liệu (Streaming SSE) |
| GET | `/api/admin/chat-logs` | Lấy lịch sử chat toàn hệ thống (Admin) |

### 📄 Documents
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/documents/upload` | Upload tài liệu (PDF/DOCX/TXT) |
| GET | `/api/documents` | Danh sách tài liệu |
| GET | `/api/documents/{id}` | Chi tiết tài liệu |
| DELETE | `/api/documents/{id}` | Xóa tài liệu |

### 📥 Ingest
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/ingest` | Bắt đầu ingest tài liệu |
| GET | `/api/ingest/status/{id}` | Kiểm tra trạng thái ingest |

---

## Biến môi trường

Trong file `micco-backend/backend/.env`:

| Biến | Mô tả | Mặc định |
|---|---|---|
| `DATABASE_URL` | Kết nối PostgreSQL | `postgresql+asyncpg://postgres:postgres@localhost:5433/nexusrag` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `CHROMA_PORT` | ChromaDB port | `8002` |
| `LLM_PROVIDER` | Provider: `gemini` hoặc `ollama` | `gemini` |
| `GOOGLE_AI_API_KEY` | API Key cho Gemini | - |
| `COHERE_API_KEY` | API Key cho Cohere Reranker | - |
| `NEXUSRAG_CHUNK_MAX_TOKENS` | Kích thước chunk tối đa | `512` |

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
<a href="#tech-stack-1">Tech Stack</a> &nbsp;|&nbsp;
<a href="#installation">Installation</a> &nbsp;|&nbsp;
<a href="#api-endpoints-1">API</a> &nbsp;|&nbsp;
<a href="#environment-variables">Env Vars</a>
</p>

</div>

---

## Overview

**miccoRAG v3** is an intelligent chatbot system using **RAG (Retrieval-Augmented Generation)** to answer questions based on document content. It leverages a hybrid approach combining Vector Search and Knowledge Graphs for superior accuracy.

| Feature | Description |
|---|---|
| 📄 **Document Upload** | Supports PDF, DOCX, TXT |
| 🧩 **Chunking & Embedding** | Auto-split documents, generate vector embeddings (BAAI/bge-m3) |
| 💬 **Smart Chat** | Answers with document context, with citations |
| 🔄 **Streaming Response** | Smooth, real-time chat experience |
| 🔍 **Hybrid Search** | Vector search + Reranking (Cohere rerank-multilingual-v3.0) |
| ⚡ **Fast LLM** | Gemini 2.5 Flash / Ollama — fast & cost-effective |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React 19 + Vite)               │
│             Chat UI · Document Upload · Dashboard            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  Auth · Chat · Documents · Ingest · Knowledge · Admin       │
└────────────┬─────────────┬──────────────┬────────────────────┘
             │             │              │
    ┌────────▼────┐ ┌───────▼──────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │  LightRAG   │ │  ChromaDB   │
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
│   ├── backend/            # FastAPI source code
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic layer
│   │   ├── models/         # SQLAlchemy models
│   │   └── ...
│   ├── docker/             # Docker compose files (Postgres, Chroma)
│   ├── setup.sh            # Auto-setup script (Ubuntu/Linux)
│   ├── run_bk.sh           # Run backend script (Ubuntu/Linux)
│   └── run_bk.bat          # Run backend script (Windows)
│
├── micco-frontend/         # 🎨 React frontend
│   ├── src/                # React source code
│   └── package.json        # Frontend dependencies
│
├── LICENSE                 # MIT License
└── README.md               # This file
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
| Docling | Document parsing (PDF/DOCX) |
| LightRAG | Knowledge Graph extraction |
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

#### Step 3: Frontend Setup

```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Step 4: Run

- **Backend**: `.\run_bk.bat` inside `micco-backend`.
- **Frontend**: `cd micco-frontend && npm run dev`.
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

#### Step 3: Run

- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Access**: http://localhost:5173

---

## API Endpoints

### 🔐 Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Login and get JWT Token |
| GET | `/api/auth/me` | Get current user info |

### 💬 Chat & RAG
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Chat with documents (Streaming SSE) |
| GET | `/api/admin/chat-logs` | Get all chat logs (Admin) |

### 📄 Documents
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/documents/upload` | Upload document (PDF/DOCX/TXT) |
| GET | `/api/documents` | List documents |
| GET | `/api/documents/{id}` | Document details |
| DELETE | `/api/documents/{id}` | Delete document |

### 📥 Ingest
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ingest` | Start document ingestion |
| GET | `/api/ingest/status/{id}` | Check ingestion status |

---

## Environment Variables

In `micco-backend/backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://postgres:postgres@localhost:5433/nexusrag` |
| `CHROMA_HOST` | ChromaDB host | `localhost` |
| `CHROMA_PORT` | ChromaDB port | `8002` |
| `LLM_PROVIDER` | Provider: `gemini` or `ollama` | `gemini` |
| `GOOGLE_AI_API_KEY` | API Key for Gemini | - |
| `COHERE_API_KEY` | API Key for Cohere Reranker | - |
| `NEXUSRAG_CHUNK_MAX_TOKENS` | Max chunk size | `512` |

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
