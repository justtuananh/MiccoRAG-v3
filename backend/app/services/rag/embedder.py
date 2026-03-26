from collections.abc import Sequence

from app.core.config import get_settings


class EmbeddingService:
    """Embedding service abstraction for pgvector/chromadb storage paths."""

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.embedding_model

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Return deterministic mock-safe vectors for current scaffold stage."""
        embeddings: list[list[float]] = []
        for text in texts:
            seed = float(sum(ord(ch) for ch in text) % 1000)
            embeddings.append([seed / 1000.0] * 8)
        return embeddings
