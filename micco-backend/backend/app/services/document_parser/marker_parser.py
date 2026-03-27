"""
Marker Document Parser
======================

Alternative document parser using Marker (marker-pdf) for high-quality
math/formula extraction (LaTeX via Surya), lighter GPU footprint (~2-4GB VRAM),
and broad format support (PDF, DOCX, PPTX, XLSX, EPUB, HTML, images).

Install: ``pip install marker-pdf[full]``
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.services.document_parser.base import BaseDocumentParser
from app.services.models.parsed_document import (
    ExtractedImage,
    ExtractedTable,
    EnrichedChunk,
    ParsedDocument,
)

logger = logging.getLogger(__name__)

_MARKER_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".epub"}
_LEGACY_EXTENSIONS = {".txt", ".md"}

# Default page separator used by Marker when paginate_output=True
_PAGE_SEPARATOR = "-" * 48


class MarkerDocumentParser(BaseDocumentParser):
    """
    Document parser powered by Marker (marker-pdf).

    Features:
    - Superior math/formula extraction (LaTeX via Surya)
    - Lighter GPU footprint (~2-4GB vs Docling's ~18-20GB)
    - Built-in image extraction, table → markdown, code blocks
    - Optional LLM-enhanced mode for better tables & equations
    """

    parser_name = "marker"

    def __init__(self, workspace_id: int, output_dir: Optional[Path] = None):
        super().__init__(workspace_id, output_dir)
        self._converter = None
        self._artifact_dict = None

    @staticmethod
    def supported_extensions() -> set[str]:
        return _MARKER_EXTENSIONS | _LEGACY_EXTENSIONS

    # ------------------------------------------------------------------
    # Lazy initialization
    # ------------------------------------------------------------------

    def _get_converter(self):
        """Lazy-init Marker PdfConverter with shared model artifacts."""
        if self._converter is not None:
            return self._converter

        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict
        from marker.config.parser import ConfigParser

        # Load models once (~2GB, cached across calls)
        if self._artifact_dict is None:
            logger.info("Loading Marker ML models...")
            self._artifact_dict = create_model_dict()

        config = {
            "output_format": "markdown",
            "paginate_output": True,
            "disable_image_extraction": not settings.NEXUSRAG_ENABLE_IMAGE_EXTRACTION,
        }

        # LLM-enhanced mode (better tables, equations, handwriting)
        if settings.NEXUSRAG_MARKER_USE_LLM:
            config["use_llm"] = True

        config_parser = ConfigParser(config)

        self._converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=self._artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )

        # Attach LLM service if enabled
        if settings.NEXUSRAG_MARKER_USE_LLM:
            try:
                self._converter.llm_service = config_parser.get_llm_service()
            except Exception as e:
                logger.warning(f"Failed to init Marker LLM service: {e}")

        return self._converter

    # ------------------------------------------------------------------
    # Main parse entry
    # ------------------------------------------------------------------

    def parse(
        self,
        file_path: str | Path,
        document_id: int,
        original_filename: str,
    ) -> ParsedDocument:
        path = Path(file_path)
        suffix = path.suffix.lower()
        start_time = time.time()

        if suffix in _MARKER_EXTENSIONS:
            result = self._parse_with_marker(path, document_id, original_filename)
        elif suffix in _LEGACY_EXTENSIONS:
            result = self._parse_legacy(path, document_id, original_filename)
        else:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported: {_MARKER_EXTENSIONS | _LEGACY_EXTENSIONS}"
            )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[marker] Parsed document {document_id} ({original_filename}) in {elapsed_ms}ms: "
            f"{result.page_count} pages, {len(result.chunks)} chunks, "
            f"{len(result.images)} images, {result.tables_count} tables"
        )
        return result

    # ------------------------------------------------------------------
    # Marker pipeline
    # ------------------------------------------------------------------

    def _parse_with_marker(
        self,
        file_path: Path,
        document_id: int,
        original_filename: str,
    ) -> ParsedDocument:
        """Parse with Marker for rich document extraction."""
        from marker.output import text_from_rendered

        converter = self._get_converter()

        logger.info(f"Marker converting: {file_path}")
        rendered = converter(str(file_path))
        text, ext, marker_images = text_from_rendered(rendered)

        # Extract and save images
        images = self._save_marker_images(marker_images, document_id)

        # Caption images with LLM vision
        if settings.NEXUSRAG_ENABLE_IMAGE_CAPTIONING and images:
            self._caption_images(images)

        # Clean Marker page number markers like "{0}", "{1}" from output
        markdown = re.sub(r"\n\{(\d+)\}", "", text)

        # Update image references in markdown with served URLs
        markdown = self._replace_image_refs_in_markdown(markdown, marker_images, images)

        # Extract tables from markdown
        tables = self._extract_tables_from_markdown(markdown, document_id)

        # Caption tables
        if settings.NEXUSRAG_ENABLE_TABLE_CAPTIONING and tables:
            self._caption_tables(tables)

        # Inject table captions
        markdown = self._inject_table_captions(markdown, tables)

        # Count pages from paginated output
        page_count = self._count_pages(markdown)

        # Chunk the document
        chunks = self._chunk_markdown(
            markdown, document_id, original_filename, images, tables
        )

        return ParsedDocument(
            document_id=document_id,
            original_filename=original_filename,
            markdown=markdown,
            page_count=page_count,
            chunks=chunks,
            images=images,
            tables=tables,
            tables_count=len(tables),
        )

    # ------------------------------------------------------------------
    # Image handling
    # ------------------------------------------------------------------

    def _save_marker_images(
        self,
        marker_images: dict,
        document_id: int,
    ) -> list[ExtractedImage]:
        """Save Marker-extracted images (PIL) to disk and create ExtractedImage list."""
        if not marker_images or not settings.NEXUSRAG_ENABLE_IMAGE_EXTRACTION:
            return []

        images_dir = self.output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        images: list[ExtractedImage] = []
        count = 0

        for filename, pil_image in marker_images.items():
            if count >= settings.NEXUSRAG_MAX_IMAGES_PER_DOC:
                break

            try:
                image_id = str(uuid.uuid4())
                image_path = images_dir / f"{image_id}.png"

                # Convert to RGB if needed (RGBA/P modes fail with some formats)
                if pil_image.mode in ("RGBA", "P", "LA"):
                    pil_image = pil_image.convert("RGB")

                pil_image.save(str(image_path), format="PNG")
                width, height = pil_image.size

                # Try to extract page number from filename (e.g., "page_3_image_1.png")
                page_no = self._extract_page_from_filename(filename)

                images.append(ExtractedImage(
                    image_id=image_id,
                    document_id=document_id,
                    page_no=page_no,
                    file_path=str(image_path),
                    caption="",
                    width=width,
                    height=height,
                ))
                count += 1

            except Exception as e:
                logger.warning(f"Failed to save Marker image {filename}: {e}")
                continue

        logger.info(f"Saved {len(images)} Marker images from document {document_id}")
        return images

    @staticmethod
    def _extract_page_from_filename(filename: str) -> int:
        """Try to extract page number from Marker image filenames."""
        # Marker filenames are like: "{doc_name}_page_{N}_image_{M}.png"
        match = re.search(r"page[_-]?(\d+)", filename, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0

    def _replace_image_refs_in_markdown(
        self,
        markdown: str,
        marker_images: dict,
        images: list[ExtractedImage],
    ) -> str:
        """Replace Marker image filenames in markdown with served URLs."""
        if not marker_images or not images:
            return markdown

        # Build mapping: original filename → served URL
        # Marker images dict and our images list are in the same order
        filenames = list(marker_images.keys())
        for i, img in enumerate(images):
            if i < len(filenames):
                original_name = filenames[i]
                served_url = f"/static/doc-images/kb_{self.workspace_id}/images/{img.image_id}.png"
                # Replace in markdown: ![alt](original_name) → ![alt](served_url)
                markdown = markdown.replace(f"]({original_name})", f"]({served_url})")

        return markdown

    # ------------------------------------------------------------------
    # Table extraction from markdown
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_tables_from_markdown(
        markdown: str, document_id: int
    ) -> list[ExtractedTable]:
        """Extract table blocks from markdown output."""
        tables: list[ExtractedTable] = []
        lines = markdown.split("\n")
        current_page = 1
        i = 0

        while i < len(lines):
            line = lines[i]

            # Track page numbers from page separators
            if line.strip() == _PAGE_SEPARATOR:
                current_page += 1
                i += 1
                continue

            # Detect table start
            if line.strip().startswith("|"):
                table_lines = [line]
                while i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                    i += 1
                    table_lines.append(lines[i])

                content_md = "\n".join(table_lines)

                # Count rows/cols
                data_rows = [
                    l for l in table_lines
                    if l.strip().startswith("|") and "---" not in l
                ]
                num_rows = max(0, len(data_rows) - 1)  # exclude header
                num_cols = 0
                if data_rows:
                    num_cols = len([
                        c for c in data_rows[0].split("|") if c.strip()
                    ])

                if num_rows > 0 or num_cols > 0:
                    tables.append(ExtractedTable(
                        table_id=str(uuid.uuid4()),
                        document_id=document_id,
                        page_no=current_page,
                        content_markdown=content_md,
                        num_rows=num_rows,
                        num_cols=num_cols,
                    ))

            i += 1

        if tables:
            logger.info(f"Extracted {len(tables)} tables from Marker markdown")
        return tables

    # ------------------------------------------------------------------
    # Page counting
    # ------------------------------------------------------------------

    @staticmethod
    def _count_pages(markdown: str) -> int:
        """Count pages from paginated markdown output."""
        if not markdown:
            return 0
        # Marker uses 48 hyphens as page separator
        separators = markdown.count(_PAGE_SEPARATOR)
        return separators + 1  # pages = separators + 1

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_markdown(
        self,
        markdown: str,
        document_id: int,
        original_filename: str,
        images: list[ExtractedImage] | None = None,
        tables: list[ExtractedTable] | None = None,
    ) -> list[EnrichedChunk]:
        """Chunk Marker markdown output into EnrichedChunks.

        Strategy: split by page separators first, then by headings within
        each page, respecting max_tokens. Each chunk retains page_no and
        heading context.
        """
        pages = markdown.split(_PAGE_SEPARATOR)
        chunks: list[EnrichedChunk] = []
        chunk_index = 0

        for page_idx, page_text in enumerate(pages):
            page_no = page_idx + 1
            page_text = page_text.strip()
            if not page_text:
                continue

            # Remove Marker page number markers like "{0}", "{1}", etc.
            page_text = re.sub(r"^\{(\d+)\}\s*", "", page_text)

            # Split page into sections by headings
            sections = self._split_by_headings(page_text)

            for heading_path, section_text in sections:
                if not section_text.strip():
                    continue

                # Split long sections into sub-chunks
                sub_chunks = self._split_text_by_tokens(
                    section_text,
                    max_tokens=settings.NEXUSRAG_CHUNK_MAX_TOKENS,
                )

                for sub_text in sub_chunks:
                    if not sub_text.strip():
                        continue

                    has_table = "|" in sub_text and "---" in sub_text
                    has_code = "```" in sub_text

                    contextualized = ""
                    if heading_path:
                        contextualized = " > ".join(heading_path) + ": " + sub_text[:100]

                    chunks.append(EnrichedChunk(
                        content=sub_text,
                        chunk_index=chunk_index,
                        source_file=original_filename,
                        document_id=document_id,
                        page_no=page_no,
                        heading_path=heading_path,
                        has_table=has_table,
                        has_code=has_code,
                        contextualized=contextualized,
                    ))
                    chunk_index += 1

        # Enrich chunks with image/table refs (shared logic from base)
        chunks = self._enrich_chunks_with_refs(chunks, images, tables)

        return chunks

    @staticmethod
    def _split_by_headings(text: str) -> list[tuple[list[str], str]]:
        """Split text into sections by markdown headings.

        Returns list of (heading_path, section_text) tuples.
        """
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        if not matches:
            return [([], text)]

        sections: list[tuple[list[str], str]] = []
        # Track current heading hierarchy
        heading_stack: list[tuple[int, str]] = []

        # Text before first heading
        if matches[0].start() > 0:
            pre_text = text[:matches[0].start()].strip()
            if pre_text:
                sections.append(([], pre_text))

        for i, match in enumerate(matches):
            level = len(match.group(1))  # number of #
            title = match.group(2).strip()

            # Update heading stack
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            heading_path = [h[1] for h in heading_stack]

            # Get section text (from after this heading to next heading)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            if section_text:
                sections.append((heading_path, section_text))

        return sections

    @staticmethod
    def _split_text_by_tokens(text: str, max_tokens: int = 512) -> list[str]:
        """Split text into chunks respecting approximate token limit.

        Uses a simple word-based approximation (1 token ≈ 0.75 words).
        """
        # Approximate: 1 token ≈ 4 chars for English, 2 chars for CJK
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return [text]

        # Split by paragraphs first
        paragraphs = re.split(r"\n\s*\n", text)
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 > max_chars:
                if current:
                    chunks.append(current.strip())
                # Handle paragraphs longer than max_chars
                if len(para) > max_chars:
                    # Split by sentences
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    current = ""
                    for sent in sentences:
                        if len(current) + len(sent) + 1 > max_chars:
                            if current:
                                chunks.append(current.strip())
                            current = sent
                        else:
                            current = current + " " + sent if current else sent
                else:
                    current = para
            else:
                current = current + "\n\n" + para if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text]

    # ------------------------------------------------------------------
    # Legacy fallback (TXT/MD) — same as Docling
    # ------------------------------------------------------------------

    def _parse_legacy(
        self,
        file_path: Path,
        document_id: int,
        original_filename: str,
    ) -> ParsedDocument:
        """Fallback: parse TXT/MD with legacy loader."""
        from app.services.document_loader import load_document
        from app.services.chunker import DocumentChunker

        loaded = load_document(str(file_path))
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        text_chunks = chunker.split_text(
            text=loaded.content,
            source=original_filename,
            extra_metadata={"document_id": document_id, "file_type": loaded.file_type},
        )

        chunks = [
            EnrichedChunk(
                content=tc.content,
                chunk_index=tc.chunk_index,
                source_file=original_filename,
                document_id=document_id,
                page_no=0,
            )
            for tc in text_chunks
        ]

        return ParsedDocument(
            document_id=document_id,
            original_filename=original_filename,
            markdown=loaded.content,
            page_count=loaded.page_count,
            chunks=chunks,
            images=[],
            tables_count=0,
        )
