# backend-agent — moved to a proper subagent

> This role is now a first-class, auto-routed Claude Code subagent: **`.claude/agents/backend.md`**.
> When a backend task comes up in MiccoRAG-v3 (FastAPI endpoints, RAG/LLM/Gemini, ChromaDB, SQLAlchemy
> models, migrations, backend tests), the `backend` subagent is selected automatically — it implements/
> edits the code and verifies via the harness (`harness/run.sh be`, `RUN_INTEGRATION=1` for e2e).
>
> Kept only as a pointer (referenced by legacy `.claude/settings.json`). Edit `.claude/agents/backend.md`.
