<!--
 ┌─────────────────────────────────────────────────────────────────┐
 │                         🇻🇳 TIẾNG VIỆT                          │
 └─────────────────────────────────────────────────────────────────┘
-->

---

<div align="center">

# <picture><source media="(prefers-color-scheme: light)" srcset="https://img.shields.io/badge/miccoRAG-v2-6E40FF?style=for-the-badge&labelColor=1a1a2e"><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/miccoRAG-v2-A78BFA?style=for-the-badge&labelColor=1a1a2e"><img alt="miccoRAG" src="https://img.shields.io/badge/miccoRAG-v2-A78BFA?style=for-the-badge&labelColor=1a1a2e"></picture> <picture><source media="(prefers-color-scheme: light)" srcset="https://img.shields.io/badge/RAG%20Chatbot-FF6B35?style=for-the-badge&labelColor=1a1a2e"><source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/RAG%20Chatbot-FF8C61?style=for-the-badge&labelColor=1a1a2e"><img alt="RAG Chatbot" src="https://img.shields.io/badge/RAG%20Chatbot-FF8C61?style=for-the-badge&labelColor=1a1a2e"></picture>

### Hệ thống RAG (Retrieval-Augmented Generation) Chatbot & Document Q&A

*Hỗ trợ tải lên, xử lý và trả lời câu hỏi dựa trên tài liệu nội bộ*

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-008C99?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)

<p>
<a href="#tổng-quan">Tổng quan</a> &nbsp;|&nbsp;
<a href="#cấu-trúc-dự-án">Cấu trúc</a> &nbsp;|&nbsp;
<a href="#tech-stack">Tech Stack</a> &nbsp;|&nbsp;
<a href="#hướng-dẫn-cài-ặt">Cài đặt</a> &nbsp;|&nbsp;
<a href="#chạy-dự-án">Chạy</a> &nbsp;|&nbsp;
<a href="#api-endpoints">API</a> &nbsp;|&nbsp;
<a href="#biến-môi-trường">Env Vars</a>
</p>

*[View in English ↓](#english-version)*

</div>

---

## Tổng quan

**miccoRAG** là hệ thống chatbot thông minh sử dụng kỹ thuật **RAG (Retrieval-Augmented Generation)** để trả lời câu hỏi dựa trên nội dung tài liệu. Hệ thống hỗ trợ:

| Chức năng | Mô tả |
|---|---|
| 📄 **Upload tài liệu** | Hỗ trợ PDF, DOCX, TXT |
| 🧩 **Tách chunk & Embedding** | Tự động tách tài liệu, tạo vector embedding |
| 💬 **Chat thông minh** | Trả lời với ngữ cảnh tài liệu, có nguồn trích dẫn |
| 🕸️ **Knowledge Graph** | Trích xuất & liên kết thực thể bằng Neo4j |
| 🔄 **Streaming response** | Trải nghiệm chat mượt mà, real-time |
| ✅ **Phê duyệt nội dung** | Workflow phê duyệt cho quản lý tài liệu |

### Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│              Chat UI · Document Upload · Dashboard           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  Auth · Chat · Documents · Ingest · Knowledge · Admin       │
└────────────┬─────────────┬──────────────┬──────────────────┘
             │             │              │
    ┌────────▼────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │  Neo4j     │ │  ChromaDB   │
    │ + pgvector  │ │  Graph DB  │ │ Vector Store│
    │ (documents) │ │  (entities)│ │ (embeddings)│
    └─────────────┘ └────────────┘ └─────────────┘
             │
    ┌────────▼────────┐
    │   LLM Providers  │
    │  OpenAI / Gemini │
    └──────────────────┘
```

---

## Cấu trúc dự án

```
miccoRAG/
│
├── MiccoRAG-v2/           # 🐳 Docker-based production setup (chính)
│   ├── backend/           # FastAPI backend v2
│   ├── frontend/          # React/Vite frontend v2
│   ├── docker/            # Docker configs & compose files
│   └── showcase/          # Demo / showcase files
│
├── backend/               # 📐 FastAPI backend (project spec / tests)
│   ├── app/               # Structured FastAPI app
│   ├── alembic/           # DB migrations
│   └── tests/             # Backend tests
│
├── micco-server/          # ⚙️  FastAPI backend (server đang chạy hiện tại)
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic
│   │   ├── embedding_service.py      # Text embedding
│   │   ├── chunker_service.py        # Document chunking
│   │   ├── ingest_pipeline.py        # Ingestion pipeline
│   │   ├── neo4j_service.py         # Neo4j operations
│   │   ├── kg_extractor.py           # KG extraction
│   │   ├── entity_embedding_service.py
│   │   ├── ocr_pipeline.py          # OCR processing
│   │   └── agent/                    # LangGraph agent
│   ├── migrations/         # DB migration files
│   ├── kg/                # Knowledge Graph utilities
│   ├── uploads/           # Uploaded files storage
│   ├── data/              # Data files
│   └── tests/             # Backend tests
│
├── micco-frontend/        # 🎨 React frontend (frontend đang chạy hiện tại)
│   ├── src/               # React source code
│   ├── dist/              # Built output
│   └── public/            # Static assets
│
├── CLAUDE.md               # Project memory & conventions
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|---|:---:|---|
| FastAPI | 0.115 | Async REST API framework |
| Python | 3.11+ | Runtime |
| SQLAlchemy | 2.0 | ORM (async) |
| PostgreSQL | 15+ | Relational database |
| pgvector | — | Vector search (production) |
| Neo4j | 5.x | Graph database |
| ChromaDB | — | Vector store (local dev) |
| Sentence Transformers | 3.0 | Local embeddings |
| LangChain / LangGraph | 0.2+ | LLM orchestration |
| OpenAI API | — | GPT models (primary LLM) |
| PyMuPDF / pdfplumber | — | PDF parsing |
| python-docx | — | Word parsing |
| PyTorch | 2.0+ | ML models |
| JWT (python-jose) | — | Authentication |

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| Vite | Build tool |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| Tanstack Query | Data fetching & caching |
| shadcn/ui | UI component library |

### Infrastructure

| Technology | Purpose |
|---|---|
| Docker + Docker Compose | Containerization |
| Nginx | Reverse proxy |
| Alembic | DB migrations |
| pytest | Testing |

---

## Hướng dẫn cài đặt

### Yêu cầu hệ thống

| Yêu cầu | Phiên bản |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker & Docker Compose | Latest |
| PostgreSQL | 15+ (hoặc dùng Docker) |
| Neo4j | 5.x (hoặc dùng Docker) |

---

### Cách 1: Cài đặt nhanh bằng Docker *(Khuyến nghị)*

```bash
# 1. Di chuyển vào thư mục project
cd d:/AI-project/HVKTQS/miccoRAG/MiccoRAG-v2

# 2. Tạo file .env từ template
cp .env.example .env
# Chỉnh sửa .env, điền các API keys cần thiết

# 3. Khởi động toàn bộ hệ thống
docker-compose up -d

# 4. Kiểm tra trạng thái các services
docker-compose ps

# 5. Xem logs
docker-compose logs -f
```

**Services được khởi động tự động:**

| Service | Port | Mô tả |
|---|---|---|
| `backend` | 8000 | FastAPI REST API |
| `frontend` | 5173 / 3000 | React UI |
| `postgres` | 5432 | PostgreSQL + pgvector |
| `neo4j` | 7474, 7687 | Neo4j Graph DB |
| `chroma` | 8000 | ChromaDB Vector Store |
| `nginx` | 80 | Reverse proxy |

---

### Cách 2: Cài đặt thủ công (Local dev)

#### 1. Backend (micco-server)

```bash
cd micco-server

# Tạo virtual environment
uv venv --python 3.11 --relocatable
# Hoặc:
python -m venv venv

# Activate
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt

# Cài đặt database (cách 1: script)
bash setup_db.sh
# Cài đặt database (cách 2: thủ công)
psql -U postgres -c "CREATE DATABASE miccodb;"
psql -U postgres -d miccodb -f init_schema.sql

# Seed data (tùy chọn)
python seed.py
```

#### 2. Neo4j

```bash
# Chạy bằng Docker (khuyến nghị)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

#### 3. Frontend

```bash
cd micco-frontend
npm install
npm run build      # Build production
# Hoặc dev server:
npm run dev
```

---

## Chạy dự án

### Chạy bằng Docker

```bash
cd MiccoRAG-v2

# Start
docker-compose up -d

# Stop
docker-compose down

# Rebuild sau khi thay đổi code
docker-compose up -d --build

# Xem logs một service
docker-compose logs -f backend
```

**Truy cập:**

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

### Chạy thủ công

```bash
# Backend
cd micco-server
.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (terminal khác)
cd micco-frontend
npm run dev

# Tests
cd micco-server && pytest tests/ -x --tb=short
```

---

## Cấu trúc thư mục chi tiết

### micco-server/ (Backend chính)

```
micco-server/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration settings
├── auth.py              # JWT authentication
├── database.py          # SQLAlchemy engine & session
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── seed.py              # Database seeding
│
├── routers/             # API route handlers
│   ├── auth.py          # Authentication endpoints
│   ├── chat.py          # Chat / conversation
│   ├── documents.py     # Document management
│   ├── ingest.py        # Document ingestion
│   ├── knowledge.py     # Knowledge Graph
│   ├── admin.py         # Admin endpoints
│   ├── approvals.py     # Content approval
│   └── dashboard.py     # Dashboard / stats
│
├── services/            # Business logic layer
│   ├── embedding_service.py
│   ├── chunker_service.py
│   ├── ingest_pipeline.py
│   ├── neo4j_service.py
│   ├── kg_extractor.py
│   ├── entity_embedding_service.py
│   ├── ocr_pipeline.py
│   ├── ocr_pipeline_vintern.py
│   └── agent/           # LangGraph agent
│
├── kg/                  # Knowledge Graph utilities
├── migrations/           # DB migrations
├── data/                 # Data files
├── uploads/              # Uploaded files
└── tests/                # Backend tests
```

### micco-frontend/

```
micco-frontend/
├── src/
│   ├── pages/           # Page components
│   ├── components/      # Reusable UI components
│   ├── api/             # API client functions
│   ├── hooks/           # Custom React hooks
│   └── utils/           # Utility functions
├── public/              # Static assets
├── dist/                # Built output
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

### MiccoRAG-v2/ (Production)

```
MiccoRAG-v2/
├── backend/             # Backend source for Docker
├── frontend/            # Frontend source for Docker
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.services.yml
│   └── init-schema.sql
├── nginx.conf
├── Dockerfile.backend
├── Dockerfile.frontend
├── setup.sh
└── run_*.sh / run_*.bat
```

---

## API Endpoints

### 🔐 Authentication
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/auth/register` | Đăng ký tài khoản |
| POST | `/api/auth/login` | Đăng nhập, nhận JWT token |
| GET | `/api/auth/me` | Lấy thông tin user hiện tại |

### 💬 Chat
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/chat` | Gửi tin nhắn (hỗ trợ streaming) |
| GET | `/api/chat/history` | Lấy lịch sử hội thoại |

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

### 🕸️ Knowledge Graph
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/knowledge/graph` | Lấy knowledge graph data |
| GET | `/api/knowledge/entities` | Danh sách entities |
| POST | `/api/knowledge/extract` | Trích xuất entities từ text |

### 📊 Dashboard
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/dashboard/stats` | Thống kê tổng quan |

### 🛠️ Admin
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/admin/users` | Danh sách users |
| POST | `/api/admin/approvals` | Phê duyệt nội dung |

---

## Biến môi trường

### Backend (micco-server)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/miccodb

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM
OPENAI_API_KEY=sk-...
# hoặc
GOOGLE_API_KEY=...

# Vector Store
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Frontend

```bash
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=miccoRAG
```

---

## Quy ước code

| Quy tắc | Chi tiết |
|---|---|
| Python files | `snake_case` |
| JS/TS files | `camelCase` |
| Classes | `PascalCase` |
| API endpoints | `/api/{resource}` (plural nouns) |
| Env vars | `UPPER_SNAKE_CASE` |
| Backend | FastAPI async, Pydantic v2 |
| Auth | JWT Bearer token |

---

## Troubleshooting

| Lỗi | Cách xử lý |
|---|---|
| `relation does not exist` | `psql -U postgres -d miccodb -f init_schema.sql` |
| `Neo4j connection refused` | `docker start neo4j` hoặc kiểm tra `NEO4J_URI` |
| `OpenAI API key not found` | Thêm `OPENAI_API_KEY` vào file `.env` |
| Lỗi CORS | Kiểm tra `ALLOWED_ORIGINS` trong `config.py` |

---

<br>

---

<!--
 ┌─────────────────────────────────────────────────────────────────┐
 │                          🇺🇸 ENGLISH                             │
 └─────────────────────────────────────────────────────────────────┘
-->

---

<div align="center">

# miccoRAG

### RAG (Retrieval-Augmented Generation) Chatbot & Document Q&A System

*Upload, process, and answer questions based on internal documents*

<p>
<a href="#overview">Overview</a> &nbsp;|&nbsp;
<a href="#project-structure">Structure</a> &nbsp;|&nbsp;
<a href="#tech-stack-1">Tech Stack</a> &nbsp;|&nbsp;
<a href="#installation">Installation</a> &nbsp;|&nbsp;
<a href="#running-the-project">Run</a> &nbsp;|&nbsp;
<a href="#api-endpoints-1">API</a> &nbsp;|&nbsp;
<a href="#environment-variables">Env Vars</a>
</p>

</div>

---

## Overview

**miccoRAG** is an intelligent chatbot system using **RAG (Retrieval-Augmented Generation)** to answer questions based on document content. Features:

| Feature | Description |
|---|---|
| 📄 **Document Upload** | Supports PDF, DOCX, TXT |
| 🧩 **Chunking & Embedding** | Auto-split documents, generate vector embeddings |
| 💬 **Smart Chat** | Answers with document context, with citations |
| 🕸️ **Knowledge Graph** | Extract & link entities via Neo4j |
| 🔄 **Streaming Response** | Smooth, real-time chat experience |
| ✅ **Content Approval** | Approval workflow for document management |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│              Chat UI · Document Upload · Dashboard           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  Auth · Chat · Documents · Ingest · Knowledge · Admin         │
└────────────┬─────────────┬──────────────┬────────────────────┘
             │             │              │
    ┌────────▼────┐ ┌──────▼─────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │  Neo4j     │ │  ChromaDB   │
    │ + pgvector  │ │  Graph DB  │ │ Vector Store│
    │ (documents) │ │  (entities)│ │ (embeddings)│
    └─────────────┘ └────────────┘ └─────────────┘
             │
    ┌────────▼────────┐
    │   LLM Providers  │
    │  OpenAI / Gemini │
    └──────────────────┘
```

---

## Project Structure

```
miccoRAG/
│
├── MiccoRAG-v2/           # 🐳 Docker-based production setup (primary)
│   ├── backend/           # FastAPI backend v2
│   ├── frontend/          # React/Vite frontend v2
│   ├── docker/            # Docker configs & compose files
│   └── showcase/          # Demo / showcase files
│
├── backend/               # 📐 FastAPI backend (project spec / tests)
│   ├── app/               # Structured FastAPI app
│   ├── alembic/           # DB migrations
│   └── tests/             # Backend tests
│
├── micco-server/          # ⚙️  FastAPI backend (current active server)
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic
│   ├── migrations/         # DB migrations
│   ├── kg/                # Knowledge Graph utilities
│   ├── uploads/           # Uploaded files
│   ├── data/              # Data files
│   └── tests/             # Backend tests
│
├── micco-frontend/         # 🎨 React frontend (current active frontend)
│   ├── src/               # React source
│   ├── dist/              # Built output
│   └── public/            # Static assets
│
├── CLAUDE.md               # Project memory & conventions
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|---|:---:|---|
| FastAPI | 0.115 | Async REST API framework |
| Python | 3.11+ | Runtime |
| SQLAlchemy | 2.0 | ORM (async) |
| PostgreSQL | 15+ | Relational database |
| pgvector | — | Vector search (production) |
| Neo4j | 5.x | Graph database |
| ChromaDB | — | Vector store (local dev) |
| Sentence Transformers | 3.0 | Local embeddings |
| LangChain / LangGraph | 0.2+ | LLM orchestration |
| OpenAI API | — | GPT models (primary LLM) |
| PyMuPDF / pdfplumber | — | PDF parsing |
| python-docx | — | Word parsing |
| PyTorch | 2.0+ | ML models |
| JWT (python-jose) | — | Authentication |

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| Vite | Build tool |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| Tanstack Query | Data fetching & caching |
| shadcn/ui | UI component library |

### Infrastructure

| Technology | Purpose |
|---|---|
| Docker + Docker Compose | Containerization |
| Nginx | Reverse proxy |
| Alembic | DB migrations |
| pytest | Testing |

---

## Installation

### System Requirements

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker & Docker Compose | Latest |
| PostgreSQL | 15+ (or Docker) |
| Neo4j | 5.x (or Docker) |

---

### Option 1: Quick Setup with Docker *(Recommended)*

```bash
# 1. Navigate to project directory
cd d:/AI-project/HVKTQS/miccoRAG/MiccoRAG-v2

# 2. Create .env from template
cp .env.example .env
# Edit .env and fill in required API keys

# 3. Start all services
docker-compose up -d

# 4. Check service status
docker-compose ps

# 5. View logs
docker-compose logs -f
```

**Auto-started services:**

| Service | Port | Description |
|---|---|---|
| `backend` | 8000 | FastAPI REST API |
| `frontend` | 5173 / 3000 | React UI |
| `postgres` | 5432 | PostgreSQL + pgvector |
| `neo4j` | 7474, 7687 | Neo4j Graph DB |
| `chroma` | 8000 | ChromaDB Vector Store |
| `nginx` | 80 | Reverse proxy |

---

### Option 2: Manual Setup (Local dev)

#### 1. Backend (micco-server)

```bash
cd micco-server

# Create virtual environment
uv venv --python 3.11 --relocatable
# Or:
python -m venv venv

# Activate
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database (option 1: script)
bash setup_db.sh
# Setup database (option 2: manual)
psql -U postgres -c "CREATE DATABASE miccodb;"
psql -U postgres -d miccodb -f init_schema.sql

# Seed data (optional)
python seed.py
```

#### 2. Neo4j

```bash
# Run via Docker (recommended)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

#### 3. Frontend

```bash
cd micco-frontend
npm install
npm run build      # Production build
# Or dev server:
npm run dev
```

---

## Running the Project

### With Docker

```bash
cd MiccoRAG-v2

# Start
docker-compose up -d

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs for a specific service
docker-compose logs -f backend
```

**Access points:**

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

### Manual

```bash
# Backend
cd micco-server
.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd micco-frontend
npm run dev

# Tests
cd micco-server && pytest tests/ -x --tb=short
```

---

## Detailed Directory Structure

### micco-server/ (Main Backend)

```
micco-server/
├── main.py              # FastAPI entry point
├── config.py            # Configuration
├── auth.py             # JWT authentication
├── database.py         # SQLAlchemy engine
├── models.py           # SQLAlchemy models
├── schemas.py          # Pydantic schemas
├── seed.py             # DB seeding
│
├── routers/            # API route handlers
│   ├── auth.py
│   ├── chat.py
│   ├── documents.py
│   ├── ingest.py
│   ├── knowledge.py
│   ├── admin.py
│   ├── approvals.py
│   └── dashboard.py
│
├── services/           # Business logic
│   ├── embedding_service.py
│   ├── chunker_service.py
│   ├── ingest_pipeline.py
│   ├── neo4j_service.py
│   ├── kg_extractor.py
│   ├── entity_embedding_service.py
│   ├── ocr_pipeline.py
│   ├── ocr_pipeline_vintern.py
│   └── agent/          # LangGraph agent
│
├── kg/                 # KG utilities
├── migrations/         # DB migrations
├── data/               # Data files
├── uploads/            # Uploaded files
└── tests/             # Backend tests
```

### micco-frontend/

```
micco-frontend/
├── src/
│   ├── pages/          # Page components
│   ├── components/     # Reusable UI components
│   ├── api/            # API client functions
│   ├── hooks/          # Custom React hooks
│   └── utils/          # Utility functions
├── public/             # Static assets
├── dist/               # Built output
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

### MiccoRAG-v2/ (Production)

```
MiccoRAG-v2/
├── backend/            # Backend source for Docker
├── frontend/          # Frontend source for Docker
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.services.yml
│   └── init-schema.sql
├── nginx.conf
├── Dockerfile.backend
├── Dockerfile.frontend
├── setup.sh
└── run_*.sh / run_*.bat
```

---

## API Endpoints

### 🔐 Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register new account |
| POST | `/api/auth/login` | Login, receive JWT token |
| GET | `/api/auth/me` | Get current user info |

### 💬 Chat
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Send message (streaming supported) |
| GET | `/api/chat/history` | Get conversation history |

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

### 🕸️ Knowledge Graph
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/knowledge/graph` | Get KG data |
| GET | `/api/knowledge/entities` | List entities |
| POST | `/api/knowledge/extract` | Extract entities from text |

### 📊 Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/stats` | Overall statistics |

### 🛠️ Admin
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/users` | User list |
| POST | `/api/admin/approvals` | Approve content |

---

## Environment Variables

### Backend (micco-server)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/miccodb

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM
OPENAI_API_KEY=sk-...
# or
GOOGLE_API_KEY=...

# Vector Store
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Frontend

```bash
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=miccoRAG
```

---

## Code Conventions

| Rule | Details |
|---|---|
| Python files | `snake_case` |
| JS/TS files | `camelCase` |
| Classes | `PascalCase` |
| API endpoints | `/api/{resource}` (plural nouns) |
| Env vars | `UPPER_SNAKE_CASE` |
| Backend | FastAPI async, Pydantic v2 |
| Auth | JWT Bearer token |

---

## Troubleshooting

| Error | Solution |
|---|---|
| `relation does not exist` | `psql -U postgres -d miccodb -f init_schema.sql` |
| `Neo4j connection refused` | `docker start neo4j` or check `NEO4J_URI` |
| `OpenAI API key not found` | Add `OPENAI_API_KEY` to `.env` |
| CORS error | Check `ALLOWED_ORIGINS` in `config.py` |

---

<br>

<div align="center">

*[ Quay về Tiếng Việt ↑ ](#tổng-quan)*

**Made with ❤️ for RAG-powered Document Q&A**

</div>
