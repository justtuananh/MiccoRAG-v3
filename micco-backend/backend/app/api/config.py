"""
Config status endpoint — expose active LLM/embedding provider info to frontend.
"""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/status")
async def get_config_status():
    """Return active provider and model names for UI display."""
    llm_provider = settings.LLM_PROVIDER.lower()

    if llm_provider == "ollama":
        llm_model = settings.OLLAMA_MODEL
    else:
        llm_model = settings.LLM_MODEL_FAST

    kg_provider = settings.KG_EMBEDDING_PROVIDER.lower()
    kg_model = settings.KG_EMBEDDING_MODEL

    return {
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "kg_embedding_provider": kg_provider,
        "kg_embedding_model": kg_model,
        "kg_embedding_dimension": settings.KG_EMBEDDING_DIMENSION,
        "nexusrag_embedding_model": settings.NEXUSRAG_EMBEDDING_MODEL,
        "nexusrag_reranker_model": settings.NEXUSRAG_RERANKER_MODEL,
    }
