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

<p>
<a href="#tổng-quan">Tổng quan</a> &nbsp;|&nbsp;
<a href="#cấu-trúc-dự-án">Cấu trúc</a> &nbsp;|&nbsp;
<a href="#tech-stack">Tech Stack</a> &nbsp;|&nbsp;
<a href="#🚀-hướng-dẫn-cho-máy-mới-windows--ubuntu">Cài đặt</a> &nbsp;|&nbsp;
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
| ✅ **Phê duyệt nội dung** | Workflow phê duyệt cho quản trị viên |

---

## Cấu trúc dự án

```
miccoRAG/
│
├── micco-backend/          # 🐳 FastAPI backend (Docker-based)
│   ├── backend/            # FastAPI source code
│   ├── docker/             # Docker configs & compose files (Postgres, Neo4j, Chroma)
│   ├── setup.sh            # Script cài đặt tự động (Ubuntu/Linux)
│   ├── run_bk.sh           # Script chạy backend (Ubuntu/Linux)
│   └── run_bk.bat          # Script chạy backend (Windows)
│
├── micco-frontend/         # 🎨 React frontend
│   ├── src/                # React source code
│   └── package.json        # Frontend dependencies
│
└── README.md               # File này
```

---

## Tech Stack

### Backend
- **FastAPI**: REST API Framework chính.
- **SQLAlchemy & PostgreSQL**: Lưu trữ metadata và document.
- **pgvector & ChromaDB**: Lưu trữ và tìm kiếm vector embedding.
- **Neo4j**: Lưu trữ Knowledge Graph (thực thể & quan hệ).
- **Cohere / Gemini**: LLM Provider cho Chat & Reranking.

### Frontend
- **React (Vite)**: Giao diện người dùng mượt mà.
- **Tailwind CSS**: Styling giao diện.
- **Lucide React**: Hệ thống icon.

---

## 🚀 Hướng dẫn cho Máy Mới (Windows & Ubuntu)

Dưới đây là các bước để thiết lập hệ thống trên một máy tính hoàn toàn mới.

### 📋 Yêu cầu tiên quyết
1.  **Docker Desktop** (Windows) hoặc **Docker Engine** (Ubuntu).
2.  **Node.js (v18+)** & **pnpm** (`npm install -g pnpm`).
3.  **Python (3.10+)**.

---

### 🪟 Cách 1: Thiết lập trên WINDOWS

#### Bước 1: Khởi động database
Mở Windows Terminal (PowerShell hoặc CMD) tại thư mục gốc:
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
# Mở file .env và điền các API Key (COHERE_API_KEY, GOOGLE_AI_API_KEY).
```

#### Bước 3: Thiết lập Frontend
```powershell
cd ..\..\micco-frontend
pnpm install
```

#### Bước 4: Chạy hệ thống
- **Backend**: Mở Terminal mới, `cd micco-backend\backend`, chạy `.\start_server.bat`. (Hoặc dùng `run_bk.bat` ở thư mục ngoài).
- **Frontend**: Mở Terminal mới, `cd micco-frontend`, chạy `npm run dev`.
- **Truy cập**: http://localhost:5173

---

### 🐧 Cách 2: Thiết lập trên UBUNTU / LINUX

#### Bước 1: Chạy Script thiết lập tự động
Mở Terminal tại thư mục gốc:
```bash
cd micco-backend
chmod +x setup.sh run_bk.sh
./setup.sh
```
*Script này sẽ tự động: Tạo venv, cài thư viện Python, khởi động Docker Services, và cài npm packages cho frontend.*

#### Bước 2: Cấu hình
Sửa file `.env` trong thư mục `micco-backend/backend/` và điền các API Key cần thiết.

#### Bước 3: Chạy hệ thống
- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`
- **Truy cập**: http://localhost:5173

---

### 🔑 Lưu ý quan trọng về Reranker
Hệ thống sử dụng **Cohere Reranker** làm mặc định để đạt độ chính xác cao nhất cho tiếng Việt. Hãy đảm bảo bạn đã cung cấp `COHERE_API_KEY` hợp lệ trong file `.env`. Nếu không có, hệ thống sẽ sử dụng kết quả từ Vector Search truyền thống (độ chính xác thấp hơn).

---

## API Endpoints

### 🔐 Authentication
| Method | Endpoint | Mô tả |
|---|-|---|
| POST | `/api/auth/login` | Đăng nhập và lấy JWT Token |
| GET | `/api/auth/me` | Lấy thông tin người dùng hiện tại |

### 💬 Chat & RAG
| Method | Endpoint | Mô tả |
|---|-|---|
| POST | `/api/chat` | Chat với tài liệu (Streaming SSE) |
| GET | `/api/admin/chat-logs` | Lấy lịch sử chat toàn hệ thống (Admin) |

---

## Biến môi trường

Trong file `micco-backend/backend/.env`:
- `GOOGLE_AI_API_KEY`: API Key cho Gemini (Chat & Embedding).
- `COHERE_API_KEY`: API Key cho Cohere (Reranking).
- `DATABASE_URL`: Kết nối Postgres (Mặc định: `postgresql+asyncpg://postgres:postgres@localhost:5433/nexusrag`).

---

<!--
 ┌─────────────────────────────────────────────────────────────────┐
 │                          🇺🇸 ENGLISH                             │
 └─────────────────────────────────────────────────────────────────┘
-->

<div id="english-version"></div>

---

<div align="center">

# miccoRAG

### RAG (Retrieval-Augmented Generation) Chatbot & Document Q&A System

<p>
<a href="#overview">Overview</a> &nbsp;|&nbsp;
<a href="#project-structure-1">Structure</a> &nbsp;|&nbsp;
<a href="#tech-stack-1">Tech Stack</a> &nbsp;|&nbsp;
<a href="#🚀-installation-for-new-machines-windows--ubuntu">Installation</a> &nbsp;|&nbsp;
<a href="#api-endpoints-1">API</a>
</p>

</div>

---

## Overview
**miccoRAG** is an intelligent chatbot system using **RAG (Retrieval-Augmented Generation)** to answer questions based on document content. It leverages a hybrid approach combining Vector Search and Knowledge Graphs for superior accuracy.

---

## 🚀 Installation for New Machines (Windows & Ubuntu)

### 📋 Prerequisites
1.  **Docker Desktop** (Windows) or **Docker Engine** (Ubuntu).
2.  **Node.js (v18+)** & **pnpm**.
3.  **Python (3.10+)**.

---

### 🪟 Option 1: WINDOWS Setup

#### Step 1: Start Database Services
In your root project folder:
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
# Edit .env and fill in COHERE_API_KEY and GOOGLE_AI_API_KEY.
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
In your terminal:
```bash
cd micco-backend
chmod +x setup.sh run_bk.sh
./setup.sh
```

#### Step 2: Configuration
Edit `micco-backend/backend/.env` with your API keys.

#### Step 3: Run
- **Backend**: `./run_bk.sh`
- **Frontend**: `cd ../micco-frontend && npm run dev`

---

## 🔑 Reranker Note
The system defaults to **Cohere Reranker (`rerank-multilingual-v3.0`)** for high-precision multilingual retrieval. Please ensure a valid `COHERE_API_KEY` is configured in your `.env`.

---

<div align="center">

*[ Back to Vietnamese ↑ ](#tổng-quan)*

**Made with ❤️ for RAG-powered Document Q&A**

</div>
