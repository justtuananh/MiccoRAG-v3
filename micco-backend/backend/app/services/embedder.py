"""
Embedding Service
=================
Generates vector embeddings using sentence-transformers.

Default model: BAAI/bge-m3 (1024-dim, multilingual, 100+ languages).
Configurable via NEXUSRAG_EMBEDDING_MODEL in settings.
"""
from __future__ import annotations

import logging
from typing import Sequence, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    Uses sentence-transformers for local embedding generation.
    """

    # Dimension lookup for common models (used before model is loaded)
    _KNOWN_DIMS = {
        "BAAI/bge-m3": 1024,
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "paraphrase-multilingual-MiniLM-L12-v2": 384,
        "intfloat/multilingual-e5-large-instruct": 1024,
    }

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.NEXUSRAG_EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        """Lazy load the model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(
                f"Embedding model loaded: {self.model_name} "
                f"(dim={self._model.get_sentence_embedding_dimension()})"
            )
        return self._model

    @property
    def dimension(self) -> int:
        """Return the embedding dimension size."""
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return self._KNOWN_DIMS.get(self.model_name, 1024)

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not text.strip():
            raise ValueError("Cannot embed empty text")
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch."""
        if not texts:
            return []
        valid_texts = [t for t in texts if t.strip()]
        if not valid_texts:
            raise ValueError("All texts are empty")
        embeddings = self.model.encode(
            valid_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
        )
        return embeddings.tolist()

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
