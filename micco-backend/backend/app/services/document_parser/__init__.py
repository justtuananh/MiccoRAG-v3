"""
Document Parser Package
========================

Factory function to create document parsers based on config.

Usage::

    from app.services.document_parser import get_document_parser

    parser = get_document_parser(workspace_id=1)
    result = parser.parse(file_path, document_id, original_filename)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.services.document_parser.base import BaseDocumentParser


def get_document_parser(
    workspace_id: int,
    output_dir: Optional[Path] = None,
) -> BaseDocumentParser:
    """Create a document parser based on ``NEXUSRAG_DOCUMENT_PARSER`` config."""
    from app.core.config import settings

    provider = settings.NEXUSRAG_DOCUMENT_PARSER.lower()

    if provider == "marker":
        from app.services.document_parser.marker_parser import MarkerDocumentParser

        return MarkerDocumentParser(workspace_id, output_dir)

    # Default: docling
    from app.services.document_parser.docling_parser import DoclingDocumentParser

    return DoclingDocumentParser(workspace_id, output_dir)


async def warmup_document_pipeline() -> None:
    """Load the configured parser's models in the background at startup.

    Docling loads its layout/table/OCR models lazily on the first document,
    which cost ~95 s for the first upload after every worker restart. Doing it
    here (in a worker thread, so the event loop stays responsive) removes that
    cold start from the user-facing path.
    """
    import asyncio
    import logging
    import time

    from app.core.config import settings

    logger = logging.getLogger(__name__)
    provider = settings.NEXUSRAG_DOCUMENT_PARSER.lower()

    if provider != "docling":
        logger.info("Document pipeline warm-up skipped (parser=%s)", provider)
        return

    from app.services.document_parser.docling_parser import warmup_docling

    try:
        elapsed = await asyncio.to_thread(warmup_docling)
    except Exception:
        logger.exception(
            "Document pipeline warm-up failed; the first upload will pay the cold-start cost"
        )
        return
    logger.info("Document pipeline warm-up finished in %.1fs", elapsed)


__all__ = [
    "get_document_parser",
    "BaseDocumentParser",
]
