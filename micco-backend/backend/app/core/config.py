from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from pathlib import Path

# Find .env file - check project root first, fallback for Docker
_candidate = Path(__file__).resolve().parent.parent.parent.parent / ".env"
ENV_FILE = str(_candidate) if _candidate.exists() else ".env"


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NexusRAG"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Base directory (backend folder)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5433/nexusrag")

    # LLM Provider: "gemini" | "ollama"
    LLM_PROVIDER: str = Field(default="gemini")

    # Google AI
    GOOGLE_AI_API_KEY: str = Field(default="")

    # Ollama
    OLLAMA_HOST: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="gemma3:12b")
    OLLAMA_ENABLE_THINKING: bool = Field(default=False)

    # LLM (fast model for chat + KG extraction — used when provider=gemini)
    LLM_MODEL_FAST: str = Field(default="gemini-2.5-flash")

    # Thinking level for Gemini 3.x+ models: "minimal" | "low" | "medium" | "high"
    # Gemini 2.5 uses thinking_budget_tokens instead (auto-detected)
    LLM_THINKING_LEVEL: str = Field(default="medium")

    # Max output tokens for LLM chat responses (includes thinking tokens)
    # Gemini 3.1 Flash-Lite supports up to 65536
    LLM_MAX_OUTPUT_TOKENS: int = Field(default=8192)

    # KG Embedding provider (can differ from LLM provider)
    KG_EMBEDDING_PROVIDER: str = Field(default="gemini")
    KG_EMBEDDING_MODEL: str = Field(default="gemini-embedding-001")
    KG_EMBEDDING_DIMENSION: int = Field(default=3072)

    # ChromaDB
    CHROMA_HOST: str = Field(default="localhost")
    CHROMA_PORT: int = Field(default=8002)

    # NexusRAG Pipeline
    NEXUSRAG_ENABLED: bool = True
    NEXUSRAG_ENABLE_KG: bool = True
    NEXUSRAG_ENABLE_IMAGE_EXTRACTION: bool = True
    NEXUSRAG_ENABLE_IMAGE_CAPTIONING: bool = True
    NEXUSRAG_ENABLE_TABLE_CAPTIONING: bool = True
    NEXUSRAG_MAX_TABLE_MARKDOWN_CHARS: int = 8000
    NEXUSRAG_CHUNK_MAX_TOKENS: int = 512
    NEXUSRAG_KG_QUERY_TIMEOUT: float = 30.0
    NEXUSRAG_KG_CHUNK_TOKEN_SIZE: int = 800   # Smaller chunks = faster LLM extraction per chunk
    NEXUSRAG_KG_LANGUAGE: str = "English"
    NEXUSRAG_KG_ENTITY_TYPES: list[str] = [
        "Organization", "Person", "Product", "Location", "Event",
        "Financial_Metric", "Technology", "Date", "Regulation",
    ]
    NEXUSRAG_DEFAULT_QUERY_MODE: str = "hybrid"
    NEXUSRAG_DOCLING_IMAGES_SCALE: float = 2.0
    NEXUSRAG_MAX_IMAGES_PER_DOC: int = 50
    NEXUSRAG_ENABLE_FORMULA_ENRICHMENT: bool = True

    # Document Parser provider: "docling" (default) or "marker" (lighter, better math)
    NEXUSRAG_DOCUMENT_PARSER: str = "docling"
    NEXUSRAG_MARKER_USE_LLM: bool = False

    # Processing timeout (minutes) — stale documents auto-recover to FAILED
    NEXUSRAG_PROCESSING_TIMEOUT_MINUTES: int = 10

    # Pre-ingestion Deduplication
    NEXUSRAG_DEDUP_ENABLED: bool = True
    NEXUSRAG_DEDUP_MIN_CHUNK_LENGTH: int = 50       # min meaningful chars
    NEXUSRAG_DEDUP_NEAR_THRESHOLD: float = 0.85     # Jaccard similarity cutoff

    # NexusRAG Retrieval Quality
    NEXUSRAG_EMBEDDING_MODEL: str = "gemini"
    NEXUSRAG_RERANKER_MODEL: str = "rerank-multilingual-v3.0"
    COHERE_API_KEY: str = Field(default="")
    NEXUSRAG_VECTOR_PREFETCH: int = 20
    NEXUSRAG_RERANKER_TOP_K: int = 8
    NEXUSRAG_MIN_RELEVANCE_SCORE: float = 0.15

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    # Compatibility auth (micco-server parity)
    JWT_SECRET_KEY: str = Field(default="change-me-in-env")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)

    # Default workspace used by /api/chat compatibility routes
    COMPAT_DEFAULT_WORKSPACE_ID: int = Field(default=1)
    COMPAT_AUTO_CREATE_DEFAULT_WORKSPACE: bool = Field(default=True)
    COMPAT_DEFAULT_WORKSPACE_NAME: str = Field(default="Default Workspace")
    COMPAT_DEFAULT_WORKSPACE_DESCRIPTION: str = Field(default="Auto-created workspace for compatibility chat APIs")
    COMPAT_ENABLE_LEGACY_ROUTES: bool = Field(default=True)
    COMPAT_ENABLE_OPEN_REGISTRATION: bool = Field(default=True)
    COMPAT_ADMIN_EMAILS: list[str] = Field(default=[])
    COMPAT_MANAGER_EMAILS: list[str] = Field(default=[])
    COMPAT_DEFAULT_USER_ROLE: str = Field(default="Nhân viên")
    COMPAT_BCRYPT_MAX_BYTES: int = Field(default=72)
    COMPAT_ADMIN_STORAGE_USE_WORKSPACE_DOCS: bool = Field(default=True)
    COMPAT_CHAT_HISTORY_SCOPE: str = Field(default="workspace")
    COMPAT_CHAT_STREAM_ENABLED: bool = Field(default=False)
    COMPAT_KEEP_LEGACY_GRAPH_DATA_FIELD: bool = Field(default=True)
    COMPAT_LEGACY_SOURCES_AS_TEXT: bool = Field(default=True)
    COMPAT_LEGACY_DOCUMENTS_USE_RAG_UPLOADS: bool = Field(default=True)
    COMPAT_LEGACY_APPROVALS_ENABLE: bool = Field(default=False)
    COMPAT_LEGACY_KNOWLEDGE_ENABLE: bool = Field(default=False)
    COMPAT_LEGACY_DASHBOARD_ENABLE: bool = Field(default=True)

    # Compatibility auth (micco-server parity)
    JWT_SECRET_KEY: str = Field(default="change-me-in-env")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)

    # Default workspace used by /api/chat compatibility routes
    COMPAT_DEFAULT_WORKSPACE_ID: int = Field(default=1)
    COMPAT_AUTO_CREATE_DEFAULT_WORKSPACE: bool = Field(default=True)
    COMPAT_DEFAULT_WORKSPACE_NAME: str = Field(default="Default Workspace")
    COMPAT_DEFAULT_WORKSPACE_DESCRIPTION: str = Field(default="Auto-created workspace for compatibility chat APIs")
    COMPAT_ENABLE_LEGACY_ROUTES: bool = Field(default=True)
    COMPAT_ENABLE_OPEN_REGISTRATION: bool = Field(default=True)
    COMPAT_ADMIN_EMAILS: list[str] = Field(default=[])
    COMPAT_MANAGER_EMAILS: list[str] = Field(default=[])
    COMPAT_DEFAULT_USER_ROLE: str = Field(default="Nhân viên")
    COMPAT_BCRYPT_MAX_BYTES: int = Field(default=72)
    COMPAT_ADMIN_STORAGE_USE_WORKSPACE_DOCS: bool = Field(default=True)
    COMPAT_CHAT_HISTORY_SCOPE: str = Field(default="workspace")
    COMPAT_CHAT_STREAM_ENABLED: bool = Field(default=False)
    COMPAT_KEEP_LEGACY_GRAPH_DATA_FIELD: bool = Field(default=True)
    COMPAT_LEGACY_SOURCES_AS_TEXT: bool = Field(default=True)
    COMPAT_LEGACY_DOCUMENTS_USE_RAG_UPLOADS: bool = Field(default=True)
    COMPAT_LEGACY_APPROVALS_ENABLE: bool = Field(default=False)
    COMPAT_LEGACY_KNOWLEDGE_ENABLE: bool = Field(default=False)
    COMPAT_LEGACY_DASHBOARD_ENABLE: bool = Field(default=True)

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
