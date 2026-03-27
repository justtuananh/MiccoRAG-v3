"""
NexusRAG Data Models
===================

Dataclasses for the NexusRAG pipeline: document parsing, enriched chunks,
citations, and retrieval results.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractedImage:
    """An image extracted from a document by Docling."""
    image_id: str
    document_id: int
    page_no: int
    file_path: str
    caption: str = ""
    width: int = 0
    height: int = 0
    bbox: Optional[tuple[float, float, float, float]] = None  # x0, y0, x1, y1
    mime_type: str = "image/png"


@dataclass
class ExtractedTable:
    """A table extracted from a document by Docling."""
    table_id: str
    document_id: int
    page_no: int
    content_markdown: str  # table.export_to_markdown(doc)
    caption: str = ""      # LLM-generated description
    num_rows: int = 0
    num_cols: int = 0


@dataclass
class EnrichedChunk:
    """A document chunk enriched with structural metadata."""
    content: str
    chunk_index: int
    source_file: str
    document_id: int
    page_no: int = 0
    heading_path: list[str] = field(default_factory=list)
    image_refs: list[str] = field(default_factory=list)  # image_ids nearby
    table_refs: list[str] = field(default_factory=list)  # table_ids nearby
    has_table: bool = False
    has_code: bool = False
    contextualized: str = ""  # heading_path joined for context


@dataclass
class ParsedDocument:
    """Result of parsing a document with Docling."""
    document_id: int
    original_filename: str
    markdown: str
    page_count: int
    chunks: list[EnrichedChunk] = field(default_factory=list)
    images: list[ExtractedImage] = field(default_factory=list)
    tables: list[ExtractedTable] = field(default_factory=list)
    tables_count: int = 0


@dataclass
class Citation:
    """A source citation pointing to a specific location in a document."""
    source_file: str
    document_id: int
    page_no: int = 0
    heading_path: list[str] = field(default_factory=list)

    def format(self) -> str:
        """Format citation as a human-readable string."""
        parts = [self.source_file]
        if self.page_no > 0:
            parts.append(f"p.{self.page_no}")
        if self.heading_path:
            parts.append(" > ".join(self.heading_path))
        return " | ".join(parts)


@dataclass
class DeepRetrievalResult:
    """Result of a deep RAG query with citations and KG insights."""
    chunks: list[EnrichedChunk]
    citations: list[Citation]
    context: str  # assembled context for LLM
    query: str
    mode: str = "hybrid"
    knowledge_graph_summary: str = ""
    image_refs: list[ExtractedImage] = field(default_factory=list)
    table_refs: list[ExtractedTable] = field(default_factory=list)
