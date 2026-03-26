from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RAG Chatbot API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    openai_api_key: str = ""
    google_api_key: str = ""
    database_url: str = "postgresql+asyncpg://user:pass@localhost/ragdb"
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    llm_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 512
    chunk_overlap: int = 50


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
