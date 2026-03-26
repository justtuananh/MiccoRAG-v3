from app.services.rag.chunker import DocumentChunker


def test_chunk_text_with_empty_input_returns_empty_list():
    chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)

    result = chunker.chunk_text("   ")

    assert result == []


def test_chunk_text_with_long_text_returns_multiple_chunks():
    chunker = DocumentChunker(chunk_size=30, chunk_overlap=5)
    text = " ".join(["word"] * 80)

    result = chunker.chunk_text(text)

    assert len(result) > 1
