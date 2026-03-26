from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings


class DocumentChunker:
    """Create text chunks for retrieval and embeddings."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None) -> None:
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def chunk_text(self, text: str) -> list[str]:
        if not text.strip():
            return []
        return self._splitter.split_text(text)
