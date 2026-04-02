# CLAUDE.md — miccoRAG v3 Project Memory

> **Project**: miccoRAG v3 — RAG Chatbot & Document Q&A System
> **Language**: Code in English; comments can be Vietnamese
> **Last updated**: 2026-04-02

---

## 🗂️ Directory Structure Overview

```
miccoRAG-v3/
│
├── micco-backend/              # FastAPI backend (NexusRAG)
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/            # v2 API routers (workspaces, documents, rag, config, expert)
│   │   │   ├── api_compat/     # Legacy compat routers (auth, admin, chat, docs, approvals, knowledge, dashboard)
│   │   │   ├── core/           # config, database, security, deps, exceptions, rls
│   │   │   ├── models/         # SQLAlchemy models (9 models)
│   │   │   ├── schemas/        # Pydantic v2 schemas (compat, document, workspace, rag)
│   │   │   ├── services/      # Business logic (12 service modules + llm package + document_parser package)
│   │   │   └── main.py         # FastAPI app entry point
│   │   ├── alembic/versions/   # 4 migration files
│   │   ├── tests/unit/         # Unit tests
│   │   ├── seed_data.py        # Seeds 4 departments + user assignments
│   │   ├── seed_users.py       # Seeds admin + 3 users
│   │   └── .env                # Local config (NOT committed)
│   ├── docker/
│   │   └── init-schema.sql     # PostgreSQL init script
│   ├── docker-compose.services.yml  # PostgreSQL 5435 + ChromaDB 8003
│   ├── docker-compose.nginx.yml    # Nginx reverse proxy
│   ├── setup.sh                # Auto-setup script (Ubuntu)
│   ├── run_bk.sh               # Backend run script
│   ├── Dockerfile.backend
│   └── .env.example
│
├── micco-frontend/             # React 19 + Vite frontend
│   ├── src/
│   │   ├── App.jsx             # Root: routing, auth, theme providers
│   │   ├── main.jsx            # React entry
│   │   ├── pages/              # 13 page components
│   │   ├── components/         # 8 component categories (admin, chat, dashboard, document-view, knowledge, landing, shared)
│   │   ├── layouts/            # DashboardLayout.jsx (sidebar nav)
│   │   ├── context/            # AuthContext.jsx, ThemeContext.jsx
│   │   ├── utils/api.js        # Centralized API service layer (ragFetch, ragFetchV2, SSE stream reader)
│   │   ├── assets/             # Logo, react.svg
│   │   ├── data/               # Static data
│   │   └── index.css           # Global styles + Tailwind
│   ├── index.html
│   ├── vite.config.js          # Vite config: proxy to Cloudflare backend, port 5174
│   ├── tailwind.config.js      # Custom colors (primary, secondary, accent), animations, typography plugin
│   ├── postcss.config.js
│   ├── eslint.config.js
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
│
├── micco-server/               # Standalone legacy backend (auth/admin/knowledge/dashboard)
│   ├── routers/                # FastAPI routers (chat, documents, ingest, agents)
│   ├── services/               # kg_service, neo4j_service, ingest_service, ocr_pipeline
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── auth.py                 # JWT auth
│   ├── config.py               # Config
│   ├── database.py             # DB connection
│   ├── main.py                 # FastAPI app
│   ├── seed.py                 # DB seeding
│   ├── init_schema.sql         # Schema initialization
│   ├── ekg/                    # Enterprise Knowledge Graph data
│   ├── kg/                     # Knowledge graph related files
│   ├── abc/                    # ABC analysis/classification data
│   ├── tests/                  # Unit tests
│   ├── uploads/                # Uploaded files directory
│   ├── data/                   # Static data
│   ├── migrations/             # DB migrations
│   ├── requirements.txt
│   ├── pytest.ini
│   └── conftest.py
│
├── .claude/
│   ├── rules/
│   │   ├── frontend.md         # Frontend dev rules (React/Vite patterns)
│   │   ├── api-design.md       # API design rules (v1 prefix, response wrapping, versioning)
│   │   ├── llm-integration.md  # LLM provider abstraction, streaming, token tracking
│   │   ├── rag-pipeline.md     # Chunking, embedding, retrieval pipeline rules
│   │   ├── testing.md          # Test structure, fixtures, naming conventions
│   │   └── multi-agent.md      # Multi-agent coordination rules
│   ├── commands/               # Claude Code skill definitions
│   │   ├── backend-dev.md      # Backend development (TDD workflow)
│   │   ├── frontend-dev.md     # Frontend development
│   │   ├── qa-tester.md        # QA testing to 95% pass
│   │   ├── coordinate-task.md  # Coordinate multiple agents
│   │   ├── run-qa.md           # Run QA tests
│   │   ├── rag-test.md         # End-to-end RAG pipeline test
│   │   └── add-provider.md     # Add new LLM provider
│   ├── backend-agent.md        # Backend dev agent definition
│   ├── frontend-agent.md       # Frontend dev agent definition
│   └── qa-agent.md             # QA tester agent definition
│
├── README.md                   # Full project documentation (Vietnamese + English)
├── CLAUDE.md                   # This file
├── LICENSE                     # MIT License
└── benchmark_report.md         # Performance benchmarks
```

---

## 🏗️ Architecture Decisions

### Dual-Backend Architecture
The project has **two backends** sharing the same database:

| | **micco-backend** (NexusRAG) | **micco-server** (Legacy) |
|---|---|---|
| Purpose | Knowledge Base + RAG + Workspaces | Auth + Admin + Knowledge + Dashboard |
| Port | 8000 | 8000 (separate) |
| API prefix | `/api/v1/...` | `/api/...` (no version) |
| DB | PostgreSQL (same instance) | PostgreSQL (same instance) |
| Docs URL | `/docs` | `/docs` |
| Used by frontend | ✅ Primary (workspaces, documents, chat, RAG) | ✅ Compatibility (auth, admin, approvals) |

**Frontend API Integration** (`src/utils/api.js`):
- `ragFetch()` → micco-server (legacy endpoints): auth, admin, approvals, documents (v1)
- `ragFetchV2()` → micco-backend (NexusRAG): workspaces, RAG processing, chat streaming
- `readSSEStream()` → SSE/NDJSON parser for streaming chat responses

### Database
- **PostgreSQL 5435** (Docker): primary relational store for all models
- **ChromaDB 8003** (Docker): vector store for embeddings
- Tables auto-created by FastAPI lifespan on startup (`AUTO_CREATE_TABLES=true`)
- Alembic migrations also available: `cd micco-backend/backend && alembic upgrade head`

### Frontend Routing
React Router v7 with two-level nesting:
```
/ (redirect) → /login
/login, /register (PublicOnlyRoute)
/dashboard, /documents, /documents/:id, /chat, /expert,
  /knowledge, /graph-knowledge, /admin, /departments,
  /approvals, /processing-status (ProtectedRoute → DashboardLayout)
```

---

## 🔑 Key Configuration Files

### Backend Environment (`micco-backend/backend/.env`)
Critical variables (defaults from `micco-backend/.env.example`):
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5435/nexusrag
CHROMA_HOST=localhost
CHROMA_PORT=8003
LLM_PROVIDER=gemini|ollama
GOOGLE_AI_API_KEY=<key>
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:12b
LLM_MODEL_FAST=gemini-2.5-flash
LLM_THINKING_LEVEL=medium
LLM_MAX_OUTPUT_TOKENS=8192
KG_EMBEDDING_PROVIDER=gemini|ollama|sentence_transformers
KG_EMBEDDING_MODEL=gemini-embedding-001
KG_EMBEDDING_DIMENSION=3072
NEXUSRAG_ENABLED=true
NEXUSRAG_ENABLE_KG=true
NEXUSRAG_CHUNK_MAX_TOKENS=512
COHERE_API_KEY=<reranker key>
JWT_SECRET_KEY=<secret>
COMPAT_ENABLE_LEGACY_ROUTES=true
CORS_ORIGINS=["http://localhost:5174","http://localhost:3000"]
```

### Frontend Environment
- `VITE_API_BASE_URL` — base URL for micco-server API (empty = use Vite proxy)
- `VITE_RAGV2_BASE_URL` — base URL for micco-backend API
- `VITE_SKIP_AUTH=true` — bypass auth in dev (returns first DB user as Admin)
- Vite dev server port: **5174** (configured in `vite.config.js`)
- Vite proxies `/api` → Cloudflare URL in dev

---

## 🧩 Key Models (SQLAlchemy)

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | id, name, email, hashed_password, role, department_id, avatar |
| `Department` | `departments` | id, name, description |
| `KnowledgeBase` | `knowledge_bases` | id, name, description, system_prompt, kg_language, kg_entity_types, search_mode, suggested_questions |
| `Document` | `documents` | Core document with status enum (PENDING→PARSING→PROCESSING→INDEXING→INDEXED/FAILED), approval_status, markdown_content, page_count, image_count, table_count, chunk_count |
| `DocumentImage` | `document_images` | Extracted images with caption, dimensions, page_no |
| `DocumentTable` | `document_tables` | Extracted tables with markdown content, caption |
| `DocumentVersion` | `document_versions` | Version history with version_number, change_note |
| `ChatMessage` | `chat_messages` | Per-workspace chat history (id, workspace_id, user_id, message_id, role, content, sources, related_entities, image_refs, thinking, ratings, created_at) |
| `SystemChatLog` | `system_chat_logs` | System-wide chat logs (workspace_id, ip_address, timestamp, response_time, question, answer, method) |
| `KnowledgeEntry` | `knowledge_entries` | User-created knowledge articles for KG |

### Document Status Enum
```
PENDING → PARSING → PROCESSING → INDEXING → INDEXED
                                              ↘ FAILED
```

### Roles (RBAC)
- `Admin` — full access
- `Trưởng phòng` — manage/dept + approve docs in their department
- `Nhân viên` — regular user, upload needs approval

---

## 🔌 API Routing Structure

### v2 API (`/api/v1/*`) — micco-backend (NexusRAG)

| Router | Prefix | Files | Purpose |
|---|---|---|---|
| `api_router` | `/api/v1` | `router.py` | Aggregator |
| `workspaces_router` | `/api/v1/workspaces` | `workspaces.py` | KnowledgeBase CRUD |
| `documents_router` | `/api/v1/documents` | `documents.py` | Document CRUD + upload + markdown + images + download |
| `rag_router` | `/api/v1/rag` | `rag.py` | RAG query, chat streaming, KG graph, stats, batch processing |
| `config_router` | `/api/v1/config` | `config.py` | App configuration |
| `expert_router` | `/api/v1/expert` | `expert.py` | Expert recommendation service |

### Legacy API (`/api/*`) — micco-server compat

| Router | Prefix | Purpose |
|---|---|---|
| `auth_router` | `/api/auth` | Register, login, me, departments |
| `admin_router` | `/api/admin` | User/dept management, stats, chat logs |
| `approvals_router` | `/api/approvals` | Pending docs, approve/reject |
| `documents_router` | `/api/documents` | Document CRUD (v1 style) |
| `chat_router` | `/api/chat` | Legacy chat (maps to v2 `/api/v1/rag/chat`) |
| `knowledge_router` | `/api/knowledge` | Knowledge entries |
| `dashboard_router` | `/api/dashboard` | Stats + recent docs + uploads chart |

### RAG Router Key Endpoints (`/api/v1/rag/`)
```python
POST /chat/{workspace_id}/stream        # SSE streaming chat
POST /chat/{workspace_id}               # Non-streaming chat
GET  /chat/{workspace_id}/history        # Get chat history
DELETE /chat/{workspace_id}/history     # Clear chat history
POST /query/{workspace_id}              # RAG query (retrieve chunks)
POST /process/{doc_id}                  # Process single document
POST /process-batch                      # Batch process documents
GET  /stats/{workspace_id}              # RAG statistics
GET  /graph/{workspace_id}              # Knowledge graph data
POST /rate-source                       # Rate a source citation
```

---

## 🧪 Test Structure

### Backend Tests
```
micco-backend/backend/tests/unit/test_expert_recommendation.py
  └─ Uses pytest, unittest.mock (AsyncMock, MagicMock)
  └─ Tests _cosine_to_relevance utility + recommend_experts() function
```

### micco-server Tests (more comprehensive)
```
micco-server/tests/
  test_agent_init.py, test_agent_graph.py, test_agent_intent_router.py,
  test_agent_tools.py
  test_chat_router.py, test_documents_router.py, test_ingest_router.py
  test_chunker_service.py, test_embedding_service.py
  test_kg_extractor.py, test_neo4j_service.py
  test_ingest_pipeline.py, test_ocr_pipeline.py, test_ontology.py
  conftest.py, __init__.py
```

### Running Tests
```bash
# Backend unit tests
cd micco-backend/backend
pytest tests/ -x --tb=short

# micco-server tests
cd micco-server
pytest tests/ -v

# RAG pipeline integration test (from .claude/commands/rag-test.md)
pytest tests/integration/test_rag_pipeline.py -v
```

### Claude Code Skills (Multi-Agent)
These skills coordinate multi-agent development:
- `/backend-dev` — Backend development (TDD workflow)
- `/frontend-dev` — Frontend development
- `/qa-tester` — QA testing, run to 95% pass
- `/coordinate-task` — Coordinate backend + frontend agents
- `/run-qa` — Run QA tests to 95% quality
- `/rag-test` — End-to-end RAG pipeline test
- `/add-provider` — Add new LLM provider to system
- `/simplify` — Review changed code for reuse, quality, efficiency

---

## ⚙️ Build / Run / Dev Commands

### Backend
```bash
# Start services (PostgreSQL + ChromaDB)
cd micco-backend
docker compose -f docker-compose.services.yml up -d

# Setup (Ubuntu auto-setup)
chmod +x setup.sh run_bk.sh
./setup.sh

# Manual setup
cd micco-backend/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && edit .env

# Migrations
cd micco-backend/backend
alembic upgrade head

# Seed data
cd micco-backend/backend
python seed_data.py   # Departments + user assignments
python seed_users.py  # Admin + 3 users

# Run backend (from micco-backend/)
uvicorn app.main:app --reload --port 8000
# OR
cd micco-backend && ./run_bk.sh
# OR (direct)
cd micco-backend/backend && uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd micco-frontend
pnpm install    # or npm install

# Dev server (port 5174, proxies /api to Cloudflare)
npm run dev

# Production build
npm run build

# Lint
npm run lint

# Preview production build
npm run preview
```

### Docker (Production)
```bash
# Start all services with Nginx
cd micco-backend
docker compose -f docker-compose.nginx.yml up -d

# Full production stack
docker compose up -d
```

---

## 📦 Dependencies

### Backend (`micco-backend/requirements.txt`)
**Framework**: FastAPI 0.104+, uvicorn, python-multipart  
**Database**: SQLAlchemy 2.0+ (async), asyncpg, alembic  
**Vector Store**: ChromaDB 0.4+  
**Embeddings**: sentence-transformers (BAAI/bge-m3), cohere (rerank-multilingual-v3.0)  
**Document Parsing**: docling 2.0+, Marker  
**LLM Providers**: google-genai (Gemini), ollama, lightrag-hku  
**Auth**: python-jose, bcrypt, passlib  
**Utilities**: pydantic 2.5+, pydantic-settings, httpx, aiofiles, Pillow

### Frontend (`micco-frontend/package.json`)
**React 19.2** + **Vite 7.3** + **Tailwind CSS 3.4** + **@tailwindcss/typography**  
**Routing**: react-router-dom 7.13  
**Rich Text**: Tiptap 3.20  
**Icons**: lucide-react 0.575  
**Charts**: Recharts 3.7  
**Knowledge Graph**: react-force-graph-2d 1.29  
**Doc Parsing**: mammoth 1.12 (client-side docx reading)  
**Testing**: playwright 1.58

---

## 📂 Key File Purposes

| File | Purpose |
|---|---|
| `micco-backend/backend/app/main.py` | FastAPI app factory, lifespan (auto-migrate, stale doc recovery), CORS, static files, route inclusion |
| `micco-backend/backend/app/core/config.py` | Pydantic Settings, all env vars, duplicate JWT_SECRET_KEY field (bug — harmless) |
| `micco-backend/backend/app/core/database.py` | SQLAlchemy async engine, AsyncSessionLocal, async_session_maker |
| `micco-backend/backend/app/core/security.py` | bcrypt hashing, JWT create/decode, `get_current_user` with dev-mode bypass (`token == "dev-skip"`) |
| `micco-backend/backend/app/core/deps.py` | `get_db()` dependency |
| `micco-backend/backend/app/services/llm/__init__.py` | Factory: `get_llm_provider()` + `get_embedding_provider()` |
| `micco-backend/backend/app/services/llm/gemini.py` | Gemini LLM + Gemini Embedding providers |
| `micco-backend/backend/app/services/llm/ollama.py` | Ollama LLM + Ollama Embedding providers |
| `micco-backend/backend/app/services/llm/sentence_transformer.py` | Local sentence-transformer embedding (no API key) |
| `micco-backend/backend/app/services/llm/base.py` | Abstract `LLMProvider` + `EmbeddingProvider` interfaces |
| `micco-backend/backend/app/services/rag_service.py` | NexusRAG service: process_document, delete_document |
| `micco-backend/backend/app/services/nexus_rag_service.py` | Extended NexusRAG with KG extraction, reranking |
| `micco-backend/backend/app/services/vector_store.py` | ChromaDB wrapper |
| `micco-backend/backend/app/services/chunker.py` | Text chunking (RecursiveCharacterTextSplitter) |
| `micco-backend/backend/app/services/embedder.py` | BGE-M3 embedding |
| `micco-backend/backend/app/services/reranker.py` | Cohere reranking |
| `micco-backend/backend/app/services/document_parser/` | Docling + Marker parsers with base interface |
| `micco-backend/backend/app/services/knowledge_graph_service.py` | KG extraction, graph data |
| `micco-backend/backend/app/services/expert_recommendation.py` | Expert finding via cosine similarity on user expertise |
| `micco-backend/backend/app/api/rag.py` | RAG endpoints: chat (SSE), query, process, KG graph, stats |
| `micco-backend/backend/app/api/chat_agent.py` | Agent-based chat with intent routing |
| `micco-backend/backend/app/api/chat_prompt.py` | System prompts (DEFAULT, HARD, etc.) |
| `micco-frontend/src/utils/api.js` | Centralized API: `ragFetch`, `ragFetchV2`, `readSSEStream`, domain APIs (workspacesApi, documentsApi, ragDocumentsApi, ragProcessApi, ragChatApi, approvalsApi, ragQueryApi, ragGraphApi) |
| `micco-frontend/src/context/AuthContext.jsx` | Auth state: login, register, logout, `authFetch`, dev bypass (`VITE_SKIP_AUTH`) |
| `micco-frontend/src/context/ThemeContext.jsx` | Dark/light theme toggle |
| `micco-frontend/src/layouts/DashboardLayout.jsx` | Sidebar nav (13 items), approval toast, user menu, profile modal |
| `micco-frontend/src/pages/ChatAssistant.jsx` | Main chat UI with streaming, document context panel, knowledge graph panel |
| `micco-frontend/src/pages/Documents.jsx` | Document list + upload UI |
| `micco-frontend/src/pages/GraphKnowledge.jsx` | Knowledge graph visualization |
| `micco-frontend/src/pages/Admin.jsx` | User + department management |

---

## 🐛 Known Issues / Notes

1. **`config.py` duplicate field**: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` and all `COMPAT_*` fields are defined TWICE in `Settings` class (lines ~104-127 and ~129-153). Python uses the last value. Harmless but should be cleaned up.

2. **Dev auth bypass**: When `VITE_SKIP_AUTH=true` in frontend, token is `"dev-skip"`. The backend `get_current_user()` checks for this and returns either the first DB user or a transient Admin. Makes local dev frictionless.

3. **Dual database ports**: PostgreSQL runs on port **5435** (not the default 5432) to avoid conflicts. ChromaDB runs on port **8003**.

4. **Compatibility routes enabled by default**: `COMPAT_ENABLE_LEGACY_ROUTES=true` means both the new v2 API and legacy API routes are registered on the same FastAPI instance. Frontend uses both.

5. **Static file mounting**: Document images from Docling are served from `backend/data/docling/` at `/static/doc-images/`.

6. **Document upload flow**: Upload → `DocumentStatus.PENDING` → background task → `PARSING` → `PROCESSING` → `INDEXING` → `INDEXED` (or `FAILED`). Non-admin uploads also need `approval_status=approved`.

7. **Chunk deduplication**: Pre-ingestion pipeline has noise filter + content hash + near-duplicate detection (`NEXUSRAG_DEDUP_*` env vars).

8. **Processing timeout**: Documents stuck in `PROCESSING`/`PARSING`/`INDEXING` for >10 minutes are auto-recovered to `FAILED` status on app startup.

---

## 📋 Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Python files | `snake_case.py` | `rag_service.py` |
| Python classes | `PascalCase` | `DocumentStatus` |
| Python functions/vars | `snake_case` | `get_llm_provider` |
| JS/JSX files | `PascalCase.jsx` | `ChatAssistant.jsx` |
| React components | `PascalCase` | `<DashboardLayout />` |
| API routes | `/snake_case` | `/api/v1/rag/chat` |
| Env vars | `UPPER_SNAKE_CASE` | `LLM_PROVIDER` |
| Git branches | `kebab-case` | `feature/new-chat-ui` |

---

## 🚫 Immutable Tech Decisions

> Do NOT change these without consulting the team:

1. **FastAPI with async/await** — no sync endpoints
2. **Pydantic v2** — no v1 syntax
3. **LLM provider via abstraction** — always use `get_llm_provider()`, never call providers directly
4. **ChromaDB for embeddings** (local dev), same model everywhere
5. **SSE streaming** for all chat endpoints
6. **JWT Bearer auth** — no session cookies
7. **RBAC with 3 roles** — Admin / Trưởng phòng / Nhân viên
8. **NexusRAG pipeline** for document ingestion (chunk → embed → rerank → KG)
9. **Vite proxy** for API calls in development (not CORS directly)
10. **React 19 + Vite 7** — current frontend stack
