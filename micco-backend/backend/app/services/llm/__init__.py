"""
LLM Provider Package
=====================
Factory functions to create LLM and embedding providers based on config.

Two providers keep a native, hand-tuned implementation:
  - "gemini" (gemini.py) — chat_agent.py's tool-calling flow depends on
    real google-genai Content/thought_signature objects for Gemini 3
    multi-turn reasoning; a generic string-based gateway can't carry that.
  - "ollama" (ollama.py) — local runtime with its own vision handling.

Every other provider name (openai, deepseek, anthropic, openrouter, ...)
is served through the LiteLLM gateway (litellm_provider.py). To add one,
just set LLM_PROVIDER=<name>, LLM_MODEL_FAST=<model>, and <NAME>_API_KEY
in .env — no new provider class required.

Usage::

    from app.services.llm import get_llm_provider, get_embedding_provider

    llm = get_llm_provider()          # uses LLM_PROVIDER from .env
    emb = get_embedding_provider()    # uses KG_EMBEDDING_PROVIDER from .env
"""
from __future__ import annotations

from functools import lru_cache

from app.services.llm.base import EmbeddingProvider, LLMProvider

# provider name -> Settings field holding its API key. Falls back to
# "<PROVIDER>_API_KEY" (e.g. "deepseek" -> DEEPSEEK_API_KEY) when not listed
# here; thanks to Settings' `extra = "allow"`, that field doesn't even need
# to be declared in config.py — just put it in .env.
_API_KEY_FIELD = {
    "openai": "OPENAI_API_KEY",
    "cohere": "COHERE_API_KEY",
    "ollama": None,  # local, no key
}


def _litellm_api_key(settings, provider: str) -> str:
    field = _API_KEY_FIELD.get(provider, f"{provider.upper()}_API_KEY")
    if field is None:
        return ""
    api_key = getattr(settings, field, "") or ""
    if not api_key:
        raise ValueError(
            f"{field} is required when provider={provider!r}. Add it to .env."
        )
    return api_key


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Create (and cache) the LLM provider configured via ``LLM_PROVIDER``."""
    from app.core.config import settings

    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        from app.services.llm.gemini import GeminiLLMProvider

        if not settings.GOOGLE_AI_API_KEY:
            raise ValueError("GOOGLE_AI_API_KEY is required when LLM_PROVIDER=gemini")
        return GeminiLLMProvider(
            api_key=settings.GOOGLE_AI_API_KEY,
            model=settings.LLM_MODEL_FAST,
            thinking_level=settings.LLM_THINKING_LEVEL,
        )

    if provider == "ollama":
        from app.services.llm.ollama import OllamaLLMProvider

        return OllamaLLMProvider(
            host=settings.OLLAMA_HOST,
            model=settings.OLLAMA_MODEL,
        )

    # Everything else -> LiteLLM gateway (openai, deepseek, anthropic, ...)
    from app.services.llm.litellm_provider import LiteLLMProvider

    return LiteLLMProvider(
        provider=provider,
        model=settings.LLM_MODEL_FAST,
        api_key=_litellm_api_key(settings, provider),
    )


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Create (and cache) the embedding provider for KG (LightRAG)."""
    from app.core.config import settings

    provider = settings.KG_EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        from app.services.llm.gemini import GeminiEmbeddingProvider

        if not settings.GOOGLE_AI_API_KEY:
            raise ValueError("GOOGLE_AI_API_KEY is required when KG_EMBEDDING_PROVIDER=gemini")
        return GeminiEmbeddingProvider(
            api_key=settings.GOOGLE_AI_API_KEY,
            model=settings.KG_EMBEDDING_MODEL,
        )

    if provider == "ollama":
        from app.services.llm.ollama import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(
            host=settings.OLLAMA_HOST,
            model=settings.KG_EMBEDDING_MODEL,
        )

    if provider == "sentence_transformers":
        from app.services.llm.sentence_transformer import SentenceTransformerEmbeddingProvider

        return SentenceTransformerEmbeddingProvider(
            model=settings.KG_EMBEDDING_MODEL,
        )

    # Everything else -> LiteLLM gateway (openai, cohere, ...)
    from app.services.llm.litellm_provider import LiteLLMEmbeddingProvider

    return LiteLLMEmbeddingProvider(
        provider=provider,
        model=settings.KG_EMBEDDING_MODEL,
        api_key=_litellm_api_key(settings, provider),
        dimension=settings.KG_EMBEDDING_DIMENSION,
    )


__all__ = [
    "get_llm_provider",
    "get_embedding_provider",
    "LLMProvider",
    "EmbeddingProvider",
]
