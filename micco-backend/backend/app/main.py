"""
MiccoRAG — standalone Knowledge Base + RAG application.
"""
from contextlib import asynccontextmanager
import asyncio
import httpx

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from datetime import datetime, timedelta

from sqlalchemy import text, update

from app.core.config import settings
from app.core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime_security()
    logger.info("Starting MiccoRAG API...")
    import os
    auto_create = os.environ.get("AUTO_CREATE_TABLES", "true").lower() == "true"
    if auto_create:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                # Auto-migrate: add new columns if missing
                await conn.execute(
                    text("ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS system_prompt TEXT")
                )
                # Ensure chat_messages table + indexes exist (idempotent)
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id SERIAL PRIMARY KEY,
                        workspace_id INTEGER NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        message_id VARCHAR(50) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        sources JSON,
                        related_entities JSON,
                        image_refs JSON,
                        thinking TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_chat_messages_workspace_id ON chat_messages(workspace_id)"
                ))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_chat_messages_user_id ON chat_messages(user_id)"
                ))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_chat_messages_message_id ON chat_messages(message_id)"
                ))
                await conn.execute(text(
                    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
                ))
                await conn.execute(text(
                    "ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS ratings JSON"
                ))
                # Keep enum labels compatible with SQLAlchemy Enum(DocumentStatus),
                # which binds enum member names like PENDING/PROCESSING/REJECTED.
                await conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_type t
                            JOIN pg_enum e ON t.oid = e.enumtypid
                            WHERE t.typname = 'documentstatus'
                              AND e.enumlabel = 'REJECTED'
                        ) THEN
                            ALTER TYPE documentstatus ADD VALUE 'REJECTED';
                        END IF;
                    END $$;
                """))
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_chat_logs (
                        id SERIAL PRIMARY KEY,
                        workspace_id INTEGER NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                        ip_address VARCHAR(50),
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        response_time FLOAT NOT NULL,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        method VARCHAR(50) NOT NULL
                    )
                """))
                await conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_system_chat_logs_workspace_id ON system_chat_logs(workspace_id)"
                ))
                # Auto-migrate: add workspace settings columns with safety timeouts
                await conn.execute(text("SET lock_timeout = '5s'"))
                await conn.execute(
                    text("ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS kg_language VARCHAR(50)")
                )
                await conn.execute(
                    text("ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS kg_entity_types JSON")
                )
                await conn.execute(
                    text("ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS search_mode VARCHAR(50) DEFAULT 'hybrid'")
                )
                await conn.execute(
                    text("ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS suggested_questions JSON")
                )
                # Migration: Add department_id to knowledge_bases (1:1 relationship)
                # Each department has exactly one workspace
                await conn.execute(
                    text("ALTER TABLE knowledge_bases ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL")
                )
                await conn.execute(
                    text("CREATE UNIQUE INDEX IF NOT EXISTS ix_knowledge_bases_department_id ON knowledge_bases(department_id) WHERE department_id IS NOT NULL")
                )
                logger.info("Database migration (department_id) completed or already up to date")

        except Exception as e:
            logger.error(f"Migration error during startup: {e}")
            # Continue even if migration fails to prevent deadlock/hang
        
        logger.info("Lifespan: Database tables created/verified")

    else:
        logger.info("AUTO_CREATE_TABLES=false — skipping auto-migration")
    from app.services.processing_recovery import recover_stale_processing
    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSession(engine) as recovery_session:
        recovered = await recover_stale_processing(recovery_session, settings.NEXUSRAG_PROCESSING_TIMEOUT_MINUTES)
        logger.info("Recovered abandoned ingest jobs: %s", recovered)
    from app.services.index_cleanup import maintenance_loop
    maintenance = asyncio.create_task(maintenance_loop())
    try:
        yield
    finally:
        maintenance.cancel()
        try:
            await maintenance
        except asyncio.CancelledError:
            pass
    logger.info("Shutting down...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="MiccoRAG — Knowledge Base with semantic search, knowledge graph, and LLM chat",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    async def database_check():
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def vector_check():
        async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
            response = await client.get(
                f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v2/heartbeat"
            )
            response.raise_for_status()
            if not isinstance(response.json().get("nanosecond heartbeat"), int):
                raise RuntimeError("Invalid vector heartbeat")

    results = await asyncio.gather(
        asyncio.wait_for(database_check(), timeout=3.0),
        asyncio.wait_for(vector_check(), timeout=3.0),
        return_exceptions=True,
    )
    checks = {name: not isinstance(result, BaseException)
              for name, result in zip(("database", "vector"), results)}
    healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "not_ready", "checks": checks},
    )


# API routes
from app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")

# Legacy compatibility routes (micco-server parity)
if settings.COMPAT_ENABLE_LEGACY_ROUTES:
    from app.api_compat import (
        auth_router,
        admin_router,
        dashboard_router,
        documents_router,
        chat_router,
        approvals_router,
        knowledge_router,
    )
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(approvals_router)
    app.include_router(documents_router)
    app.include_router(chat_router)
    app.include_router(knowledge_router)
    
    if getattr(settings, "COMPAT_LEGACY_DASHBOARD_ENABLE", True):
        app.include_router(dashboard_router)

# Document images are served by authenticated document routes, never a public mount.

# Import models so SQLAlchemy registers them
from app.models import knowledge_base, document, chat_message  # noqa: E402, F401
