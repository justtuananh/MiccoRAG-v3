import pytest

from app.services.rag.embedder import EmbeddingService


@pytest.mark.asyncio
async def test_embed_texts_returns_vector_per_input_text():
    service = EmbeddingService()

    vectors = await service.embed_texts(["one", "two"])

    assert len(vectors) == 2
    assert all(len(vector) == 8 for vector in vectors)
