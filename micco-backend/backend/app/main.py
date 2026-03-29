"""
MiccoRAG — standalone Knowledge Base + RAG application.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging

from datetime import datetime, timedelta

from sqlalchemy import text, update

from app.core.config import settings
from app.core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
                logger.info("Database migration (suggested_questions) completed or already up to date")

        except Exception as e:
            logger.error(f"Migration error during startup: {e}")
            # Continue even if migration fails to prevent deadlock/hang
        
        logger.info("Lifespan: Database tables created/verified")

        # Recover stale processing documents (stuck from previous runs)
        from app.models.document import Document, DocumentStatus
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select as sa_select
        async with AsyncSession(engine) as session:
            timeout = settings.NEXUSRAG_PROCESSING_TIMEOUT_MINUTES
            cutoff = datetime.utcnow() - timedelta(minutes=timeout)
            stale_statuses = [
                DocumentStatus.PROCESSING,
                DocumentStatus.PARSING,
                DocumentStatus.INDEXING,
            ]
            result = await session.execute(
                update(Document)
                .where(
                    Document.status.in_(stale_statuses),
                    Document.updated_at < cutoff,
                )
                .values(
                    status=DocumentStatus.FAILED,
                    error_message=f"Processing timeout ({timeout}min). Click Analyze to retry.",
                )
                .returning(Document.id)
            )
            stale_ids = [row[0] for row in result.fetchall()]
            if stale_ids:
                await session.commit()
                logger.warning(f"Recovered {len(stale_ids)} stale documents: {stale_ids}")
    else:
        logger.info("AUTO_CREATE_TABLES=false — skipping auto-migration")
    yield
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
    return {"status": "ready"}


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

# Static files — document images extracted by MiccoRAG (Docling)
_docling_data = Path(__file__).resolve().parent.parent / "data" / "docling"
_docling_data.mkdir(parents=True, exist_ok=True)
app.mount("/static/doc-images", StaticFiles(directory=str(_docling_data)), name="static_doc_images")

# Import models so SQLAlchemy registers them
from app.models import knowledge_base, document, chat_message  # noqa: E402, F401
