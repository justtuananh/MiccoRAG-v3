# 🚀 Claude Code Init Prompts — RAG Chatbot + Document Q&A
# Stack: FastAPI · OpenAI + Gemini · pgvector + ChromaDB · Next.js

---

## 📋 CÁCH SỬ DỤNG

Copy từng **PROMPT** theo thứ tự → paste vào Claude Code terminal.
Mỗi prompt có ký hiệu: 🔧 setup | 📝 tạo file | 🤖 giao việc cho agent

---

## BƯỚC 1 — Tạo cấu trúc thư mục .claude/

> 🔧 Chạy lệnh này trong terminal tại root project

```bash
mkdir -p .claude/rules && \
mkdir -p .claude/commands && \
touch .claude/settings.json && \
touch CLAUDE.md && \
touch .claude/rules/api-design.md && \
touch .claude/rules/rag-pipeline.md && \
touch .claude/rules/llm-integration.md && \
touch .claude/rules/testing.md && \
touch .claude/rules/frontend.md && \
echo "✅ Claude Code structure created"
```

---

## BƯỚC 2 — Tạo CLAUDE.md (bộ nhớ chính của project)

> 📝 Tạo file CLAUDE.md tại root project với nội dung sau:

```markdown
# PROJECT MEMORY — RAG Chatbot & Document Q&A

## Project Overview
- **Purpose**: RAG Chatbot system + Document Q&A (PDF/Word support)
- **Backend**: Python FastAPI (async)
- **Frontend**: React / Next.js
- **LLM Providers**: OpenAI (primary), Google Gemini (fallback/secondary)
- **Vector Store**: PostgreSQL + pgvector (production), ChromaDB (dev/local)
- **Language**: Code in English, comments can be Vietnamese

## Directory Structure
```
project-root/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── core/         # config, security, deps
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── llm/      # OpenAI + Gemini clients
│   │   │   ├── rag/      # chunking, embedding, retrieval
│   │   │   └── document/ # PDF/Word parsing
│   │   └── schemas/      # Pydantic schemas
│   ├── tests/
│   └── alembic/
├── frontend/             # Next.js app
├── .claude/
│   ├── rules/
│   ├── commands/
│   └── settings.json
└── docker-compose.yml
```

## Naming Conventions
- Files: snake_case (Python), kebab-case (Next.js)
- Classes: PascalCase
- Functions/vars: snake_case (Python), camelCase (JS/TS)
- API endpoints: /api/v1/{resource} (plural nouns)
- Env vars: UPPER_SNAKE_CASE

## Tech Decisions (không được đổi mà không hỏi)
- FastAPI với async/await — KHÔNG dùng sync endpoints
- Pydantic v2 cho validation — KHÔNG dùng v1 syntax
- pgvector cho production embeddings, ChromaDB cho local dev
- LLM provider selection qua environment variable: LLM_PROVIDER=openai|gemini
- Streaming response mặc định cho chat endpoints

## Mandatory TDD Workflow
1. Viết FAILING test trước — KHÔNG implement trước khi có test
2. Chạy test, confirm fail
3. Implement minimum code để pass
4. Chạy lại — lặp đến khi GREEN
5. Tối đa 5 iterations, sau đó báo cáo nếu không pass

## Commands hay dùng
- Run backend: `cd backend && uvicorn app.main:app --reload`
- Run tests: `cd backend && pytest tests/ -x --tb=short`
- Run frontend: `cd frontend && npm run dev`
- Docker: `docker-compose up -d`
- Migrate DB: `cd backend && alembic upgrade head`

## Environment Variables cần thiết
```
OPENAI_API_KEY=
GOOGLE_API_KEY=
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ragdb
CHROMA_HOST=localhost
CHROMA_PORT=8000
LLM_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

## Code Quality Rules
- Mọi async function phải có type hints
- Mọi API endpoint phải có docstring
- Không hardcode API keys — chỉ dùng os.getenv()
- Log mọi LLM call với: provider, model, tokens used, latency
```

---

## BƯỚC 3 — Tạo .claude/rules/ (context theo domain)

### 📝 File: .claude/rules/llm-integration.md

```markdown
# LLM Integration Rules

## Provider Architecture
Luôn dùng abstract LLMProvider interface — KHÔNG call OpenAI/Gemini trực tiếp trong business logic.

```python
# ĐÚNG — qua provider abstraction
from app.services.llm import get_llm_provider
llm = get_llm_provider()  # trả về OpenAI hoặc Gemini tùy env

# SAI — gọi trực tiếp
from openai import AsyncOpenAI
client = AsyncOpenAI()
```

## Streaming
- Mọi chat endpoint PHẢI support streaming (Server-Sent Events)
- Dùng `async for chunk in response:` pattern
- Frontend nhận stream qua EventSource

## Token Tracking
Mọi LLM call phải log:
```python
logger.info("LLM call", extra={
    "provider": provider_name,
    "model": model_name, 
    "prompt_tokens": usage.prompt_tokens,
    "completion_tokens": usage.completion_tokens,
    "latency_ms": elapsed_ms
})
```

## Error Handling
- OpenAI rate limit → retry với exponential backoff (tenacity)
- OpenAI error → fallback sang Gemini nếu LLM_FALLBACK=true
- Luôn return structured error: {"error": "...", "code": "...", "retry_after": ...}
```

### 📝 File: .claude/rules/rag-pipeline.md

```markdown
# RAG Pipeline Rules

## Chunking Strategy
- Default: RecursiveCharacterTextSplitter, chunk_size=512, overlap=50
- PDF: Ưu tiên giữ nguyên paragraph
- Code files: chunk theo function/class boundary

## Embedding
- Production: OpenAI text-embedding-3-small (1536 dims) → lưu vào pgvector
- Local dev: ChromaDB với same embedding model
- KHÔNG mix embedding models trong cùng một collection

## Retrieval
- Top-K mặc định: 5
- Reranking: CrossEncoder nếu có, skip nếu latency > 500ms
- Hybrid search: vector similarity + BM25 keyword (pgvector + pg_trgm)

## Context Assembly
```python
# Template chuẩn cho RAG context
SYSTEM_PROMPT = """You are a helpful assistant. Answer based ONLY on the provided context.
If the answer is not in the context, say "Tôi không tìm thấy thông tin này trong tài liệu."

Context:
{context}
"""
```

## Document Processing Pipeline
1. Upload → validate (PDF/DOCX/TXT only, max 50MB)
2. Extract text (PyMuPDF cho PDF, python-docx cho Word)
3. Clean text (remove headers/footers, normalize whitespace)
4. Chunk → embed → store
5. Return document_id để track
```

### 📝 File: .claude/rules/api-design.md

```markdown
# API Design Rules

## Endpoint Structure
- Base: /api/v1/
- Tất cả response wrap trong: {"data": ..., "meta": {...}}
- Error response: {"error": {"message": "...", "code": "...", "details": {}}}

## Versioning
- Luôn có /api/v1/ prefix
- Breaking changes → tạo /api/v2/, KHÔNG xóa v1 ngay

## Request/Response
```python
# Mọi endpoint phải có schema rõ ràng
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    stream: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: List[DocumentSource]
    usage: TokenUsage
```

## Auth
- JWT Bearer token cho mọi endpoint trừ /health và /docs
- Rate limiting: 60 req/min per user, 10 req/min cho /upload

## Async
- Mọi endpoint PHẢI là async def
- File upload xử lý via background task (BackgroundTasks)
```

### 📝 File: .claude/rules/testing.md

```markdown
# Testing Rules

## Test Structure
```
tests/
├── unit/
│   ├── test_rag_chunking.py
│   ├── test_llm_provider.py
│   └── test_document_parser.py
├── integration/
│   ├── test_api_chat.py
│   └── test_api_upload.py
└── conftest.py
```

## Fixtures bắt buộc (conftest.py)
- `mock_openai_client` — mock OpenAI để test không tốn tiền
- `mock_gemini_client` — mock Gemini
- `test_db` — PostgreSQL test database (dùng pytest-asyncio)
- `sample_pdf` — PDF test fixture
- `authenticated_client` — FastAPI TestClient với JWT token

## Rules
- Mock mọi external API calls (OpenAI, Gemini) trong unit tests
- Integration test dùng test database riêng (TEST_DATABASE_URL)
- Mỗi test phải cleanup data sau khi chạy
- Tên test: test_{function_name}_{scenario}_{expected_result}
  Ví dụ: test_retrieve_chunks_empty_query_returns_empty_list
```

### 📝 File: .claude/rules/frontend.md

```markdown
# Frontend Rules (Next.js)

## Stack
- Next.js 14+ App Router
- TypeScript strict mode
- Tailwind CSS
- shadcn/ui components
- Tanstack Query cho data fetching

## Chat UI
- Streaming: dùng EventSource hoặc fetch với ReadableStream
- Message format: {role: "user"|"assistant", content: string, sources?: Source[]}
- Luôn show loading skeleton khi đang fetch

## API Calls
- Mọi call qua /api/ Next.js route handlers (không call FastAPI trực tiếp từ browser)
- Error boundary cho mọi page
- Toast notification cho errors

## File Upload
- Drag & drop với react-dropzone
- Chỉ accept: PDF, DOCX, TXT
- Show progress bar khi upload
- Max 50MB client-side validation
```

---

## BƯỚC 4 — Tạo .claude/settings.json (hooks TDD auto-loop)

> 📝 Paste nội dung này vào .claude/settings.json

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "command": "cd backend && python -m pytest tests/ -x --tb=short -q 2>&1 | tail -30"
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(pytest:*)",
      "Bash(uvicorn:*)",
      "Bash(alembic:*)",
      "Bash(pip:*)",
      "Bash(npm:*)",
      "Bash(docker-compose:*)"
    ]
  }
}
```

---

## BƯỚC 5 — Tạo custom slash commands

### 📝 File: .claude/commands/rag-test.md

```markdown
---
description: Test toàn bộ RAG pipeline từ đầu đến cuối
---

Chạy end-to-end test cho RAG pipeline:
1. Upload file test (dùng fixture tests/fixtures/sample.pdf)
2. Verify chunking ra đúng số chunks
3. Verify embedding được store vào vector DB
4. Chạy query "tóm tắt nội dung tài liệu" và verify trả về context
5. Verify response có sources
6. Report kết quả và bất kỳ lỗi nào

Chạy lệnh: pytest tests/integration/test_rag_pipeline.py -v
```

### 📝 File: .claude/commands/add-provider.md

```markdown
---
description: Thêm LLM provider mới vào hệ thống
---

Để thêm LLM provider mới có tên $ARGUMENTS:
1. Tạo file backend/app/services/llm/providers/$ARGUMENTS.py
2. Implement LLMProvider abstract class
3. Thêm vào factory trong backend/app/services/llm/__init__.py
4. Thêm env var LLM_PROVIDER=$ARGUMENTS vào .env.example
5. Viết unit test trong tests/unit/test_llm_$ARGUMENTS.py
6. Update CLAUDE.md phần LLM Providers
```

---

## BƯỚC 6 — MCP Setup (chạy trong Claude Code terminal)

> 🔧 Cài đặt MCP servers cần thiết

```bash
# PostgreSQL MCP — query DB bằng ngôn ngữ tự nhiên
claude mcp add postgres-mcp npx @modelcontextprotocol/server-postgres \
  --env DATABASE_URL=$DATABASE_URL

# Playwright MCP — fix FE bugs tự động (dùng đúng version)
claude mcp add playwright npx @playwright/mcp@0.0.41

# Filesystem MCP — đọc/write files ngoài project
claude mcp add filesystem npx @modelcontextprotocol/server-filesystem \
  --arg /path/to/project
```

---

## BƯỚC 7 — PROMPT KHỞI ĐỘNG DỰ ÁN (paste vào Claude Code)

> 🤖 Đây là prompt chính — paste toàn bộ vào Claude Code sau khi setup xong bước 1–6

---

### PROMPT 7A — Khởi tạo toàn bộ project structure

```
Read CLAUDE.md and all files in .claude/rules/ first.

Then create the complete project skeleton for our RAG Chatbot + Document Q&A system:

PHASE 1 — Backend skeleton (do this first):
1. Create backend/ directory with proper Python package structure
2. Create pyproject.toml with dependencies:
   - fastapi, uvicorn[standard], pydantic[email]>=2.0
   - sqlalchemy[asyncio], asyncpg, alembic
   - pgvector, chromadb
   - openai>=1.0, google-generativeai
   - langchain-text-splitters, pymupdf, python-docx
   - pytest, pytest-asyncio, pytest-mock, httpx
   - tenacity, python-jose[cryptography], passlib
3. Create app/core/config.py — all settings from env vars (pydantic-settings)
4. Create app/main.py — FastAPI app with CORS, lifespan, /health endpoint
5. Create placeholder files for all directories in CLAUDE.md structure

PHASE 2 — LLM Provider abstraction:
1. Create abstract LLMProvider class in app/services/llm/base.py
2. Implement OpenAIProvider in app/services/llm/providers/openai.py
3. Implement GeminiProvider in app/services/llm/providers/gemini.py
4. Create factory function get_llm_provider() based on LLM_PROVIDER env var
5. Write unit tests for both providers (mock the API calls)
6. Run tests — iterate until GREEN

PHASE 3 — RAG pipeline core:
1. Create DocumentChunker in app/services/rag/chunker.py
2. Create EmbeddingService in app/services/rag/embedder.py (pgvector + chromadb)
3. Create RetrieverService in app/services/rag/retriever.py
4. Write unit tests for each component
5. Run tests — iterate until GREEN

After each phase: run pytest, fix any failures, then continue.
Report progress after each phase is complete.
```

---

### PROMPT 7B — Tích hợp GitHub repo mới vào project

```
I found this GitHub repo that might be useful for our RAG pipeline:
[PASTE GITHUB URL HERE]

Please:
1. Read the README and main source files of that repo
2. Analyze: what problem does it solve? How does it work?
3. Evaluate compatibility with our stack (FastAPI + pgvector + OpenAI/Gemini)
4. If compatible, propose an integration plan with:
   - Which existing files will be affected
   - New files/dependencies needed
   - Risks and breaking changes
   - 3 implementation phases (small, testable)
5. Wait for my approval before implementing anything

Do NOT start coding until I confirm the integration plan.
```

---

### PROMPT 7C — Auto TDD loop cho 1 feature

```
Implement the document upload endpoint following strict TDD:

Feature: POST /api/v1/documents/upload
- Accept: PDF, DOCX, TXT files (max 50MB)
- Process: validate → extract text → chunk → embed → store in pgvector
- Return: {document_id, filename, chunk_count, status}

Workflow (follow exactly):
1. Write failing test first in tests/integration/test_api_upload.py
2. Run pytest — confirm it FAILS
3. Implement minimum code to make it pass
4. Run pytest again
5. Repeat steps 3-4 until ALL tests GREEN
6. Max 5 iterations per test — if still failing after 5, stop and explain why

Rules from .claude/rules/api-design.md and .claude/rules/rag-pipeline.md apply.
Mock all external calls (OpenAI embedding API) in tests.
```

---

### PROMPT 7D — Fix FE bug với Playwright (thay thế screenshot)

```
Use Playwright MCP to debug and fix the frontend issue:

1. Navigate to http://localhost:3000
2. Take a screenshot of the current state
3. Read the browser console for any errors
4. Inspect the DOM element that has the issue: [MÔ TẢ ELEMENT]
5. Check the network tab for failed API calls
6. Based on what you find, fix the issue in the source code
7. Navigate again and take another screenshot to verify the fix
8. Run: npm run build to ensure no TypeScript errors

Do NOT ask me what the error is — find it yourself via browser inspection.
```

---

### PROMPT 7E — Multi-agent phase planning

```
I want to build the complete RAG Chatbot system. 
Read CLAUDE.md first, then create a detailed execution plan.

Use /plan mode to:
1. Break the entire system into 5 phases
2. Each phase must have:
   - Clear deliverables (list of files created/modified)
   - Acceptance criteria (specific tests that must pass)
   - Estimated complexity: S/M/L
3. Identify which phases can use sub-agents in parallel
4. Identify dependencies between phases

Format the plan as a checklist I can track.
Do NOT start implementing — just plan.
After I approve the plan, I will say "execute phase 1" to start.
```

---

## CHECKLIST KHỞI TẠO

Tick từng bước khi hoàn thành:

- [ ] **B1** — Chạy bash script tạo folder .claude/
- [ ] **B2** — Tạo CLAUDE.md với nội dung đầy đủ
- [ ] **B3** — Tạo 5 file trong .claude/rules/
- [ ] **B4** — Tạo .claude/settings.json với PostToolUse hooks
- [ ] **B5** — Tạo 2 custom slash commands
- [ ] **B6** — Cài 3 MCP servers (postgres, playwright, filesystem)
- [ ] **B7A** — Chạy prompt khởi tạo project structure
- [ ] Verify: `pytest` pass ít nhất 1 test
- [ ] Verify: `uvicorn app.main:app` chạy được
- [ ] Verify: `/health` endpoint trả về 200

---

## MẸO SỬ DỤNG HÀNG NGÀY

| Tình huống | Prompt nên dùng |
|---|---|
| Bắt đầu session mới | "Read CLAUDE.md and .claude/rules/ — summarize current project state" |
| Thêm feature mới | "Follow TDD workflow in CLAUDE.md. Feature: [mô tả]" |
| Context sắp đầy (~70%) | Gõ `/compact` trước khi tiếp tục |
| Tìm thấy repo hay | Dùng **Prompt 7B** |
| FE có bug visual | Dùng **Prompt 7D** với Playwright |
| Build phase lớn | Dùng **Prompt 7E** để plan trước |
| Custom workflow lặp lại | Tạo file mới trong `.claude/commands/` |