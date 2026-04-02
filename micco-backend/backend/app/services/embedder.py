"""
Embedding Service
=================
Generates vector embeddings using the configured embedding provider.

Delegates to `app.services.llm.get_embedding_provider()`.
"""
from __future__ import annotations

import logging
from typing import Sequence, Optional

from app.core.config import settings
from app.services.llm import get_embedding_provider

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    Proxies to the unified get_embedding_provider() which handles Gemini API calls.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.NEXUSRAG_EMBEDDING_MODEL

    @property
    def provider(self):
        """Lazy load the provider."""
        return get_embedding_provider()

    @property
    def dimension(self) -> int:
        """Return the embedding dimension size."""
        return self.provider.get_dimension()

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not text.strip():
            raise ValueError("Cannot embed empty text")
        
        # embed_sync returns a NumPy array with the shape (batch_size, dim)
        embeddings_arr = self.provider.embed_sync([text])
        return embeddings_arr[0].tolist()

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch."""
        if not texts:
            return []
        valid_texts = [t for t in texts if t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")
        
        embeddings_arr = self.provider.embed_sync(valid_texts)
        return embeddings_arr.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query."""
        return self.embed_text(query)


# Default service instance (singleton)
_default_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the default embedding service."""
    global _default_service
    if _default_service is None:
        _default_service = EmbeddingService()
    return _default_service


def embed_text(text: str) -> list[float]:
    """Convenience function to embed a single text."""
    return get_embedding_service().embed_text(text)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Convenience function to embed multiple texts."""
    return get_embedding_service().embed_texts(texts)
