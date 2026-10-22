"""
Reranker Service
================
Reranking via LiteLLM's unified rerank() API.

Default model: rerank-multilingual-v3.0 (Cohere)
Configurable via NEXUSRAG_RERANKER_MODEL in settings.

Usage:
    reranker = get_reranker_service()
    ranked = reranker.rerank("user question", ["chunk1", "chunk2", ...], top_k=5)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional, Sequence

import litellm

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """A single reranked item with its original index and relevance score."""
    index: int          # Original position in the input list
    score: float        # Cross-encoder relevance score (higher = more relevant)
    text: str           # The chunk text


class RerankerService:
    """
    LiteLLM-backed reranker service (Cohere by default).
    Fast and cost-effective reranking through the cloud.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.NEXUSRAG_RERANKER_MODEL
        self.api_key = settings.COHERE_API_KEY
        self._retry_after = 0.0

    def rerank(
        self,
        query: str,
        documents: Sequence[str],
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> list[RerankResult]:
        """
        Rerank documents by relevance to the query.

        Args:
            query: The user's search query
            documents: List of document texts to rerank
            top_k: Maximum number of results to return (None = all)
            min_score: Minimum relevance score threshold (None = no filtering)

        Returns:
            List of RerankResult sorted by score (descending),
            filtered by top_k and min_score.
        """
        if not documents:
            return []

        if not self.api_key or time.monotonic() < self._retry_after:
            selected = list(documents)[:top_k] if top_k is not None else list(documents)
            return [RerankResult(index=i, score=1.0/(i+1), text=doc) for i,doc in enumerate(selected)]

        # Ensure we don't exceed typical API limits if documents is too large
        docs_to_rerank = list(documents[:100])

        try:
            if not self.api_key:
                raise ValueError("COHERE_API_KEY is not set.")

            response = litellm.rerank(
                model=self.model_name,
                query=query,
                documents=docs_to_rerank,
                top_n=top_k if top_k is not None else len(docs_to_rerank),
                api_key=self.api_key,
            )
            # Map response back to RerankResult. LiteLLM's rerank() has returned
            # both plain dicts and objects across versions, so accept either.
            def _field(item, name):
                return item[name] if isinstance(item, dict) else getattr(item, name)

            results = [
                RerankResult(
                    index=_field(r, "index"),
                    score=_field(r, "relevance_score"),
                    text=documents[_field(r, "index")],
                )
                for r in response.results
            ]

            # Apply min_score limit
            if min_score is not None:
                results = [r for r in results if r.score >= min_score]

            return results
        except Exception as e:
            self._retry_after = time.monotonic() + (60 if getattr(e, "status_code", None) == 429 else 10)
            logger.warning("Reranker unavailable; preserving vector order: %s", type(e).__name__)
            # Fallback to returning original items with dummy/heuristic scores if rerank fails
            fallback_docs = list(documents)
            if top_k is not None:
                fallback_docs = fallback_docs[:top_k]

            return [
                RerankResult(index=i, score=1.0 / (i + 1), text=doc)
                for i, doc in enumerate(fallback_docs)
            ]


# Singleton instance
_default_service: Optional[RerankerService] = None


def get_reranker_service() -> RerankerService:
    """Get or create the default reranker service."""
    global _default_service
    if _default_service is None:
        _default_service = RerankerService()
    return _default_service
