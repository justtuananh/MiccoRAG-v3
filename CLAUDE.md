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

## Multi-Agent System

### Agent Roles
| Agent | Working Directory | Responsibilities |
|-------|------------------|-----------------|
| **backend-dev** | `/home/kms/MiccoRAG-v3/micco-backend/backend` | FastAPI, Services, Models, DB |
| **frontend-dev** | `/home/kms/MiccoRAG-v3/micco-frontend` | React, UI, API integration |
| **qa-tester** | `/home/kms/micco` | Testing, Quality Assurance |

### Workflow
1. **User giao task** → Main agent analyze và coordinate
2. **Backend dev** → Implement backend (TDD workflow)
3. **Frontend dev** → Implement frontend (sau khi backend ready)
4. **QA tester** → Run tests nhiều lần đến khi **95% pass**
5. **Report** → Final quality report

### Commands
```bash
/coordinate-task  # Phối hợp 2 agent
/run-qa           # Chạy QA tests đạt 95%
/backend-dev      # Backend development
/frontend-dev     # Frontend development
```

### Quality Gates
- Test pass rate ≥ 95%
- Test coverage ≥ 80%
- Critical bugs = 0
- No hardcoded secrets
