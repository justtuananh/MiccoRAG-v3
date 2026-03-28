"""
Reranker Service
================
Cohere reranker for improving retrieval precision.

Default model: rerank-multilingual-v3.0
Configurable via NEXUSRAG_RERANKER_MODEL in settings.

Usage:
    reranker = get_reranker_service()
    ranked = reranker.rerank("user question", ["chunk1", "chunk2", ...], top_k=5)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Sequence
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
    Cohere API-based reranker service.
    Fast and cost-effective reranking through the cloud.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.NEXUSRAG_RERANKER_MODEL
        self.api_key = settings.COHERE_API_KEY
        self._client = None

    @property
    def client(self):
        """Lazy load the Cohere client."""
        if self._client is None:
            import cohere
            logger.info(f"Init Cohere Client for reranker: {self.model_name}")
            if not self.api_key:
                logger.error("COHERE_API_KEY is missing from environment variables/config.")
                raise ValueError("COHERE_API_KEY is not set.")
            self._client = cohere.ClientV2(self.api_key)
        return self._client

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

        # Ensure we don't exceed typical API limits if documents is too large
        docs_to_rerank = list(documents[:100])

        try:
            response = self.client.rerank(
                model=self.model_name,
                query=query,
                documents=docs_to_rerank,
                top_n=top_k if top_k is not None else len(docs_to_rerank)
            )
            # Map Cohere response back to RerankResult
            results = [
                RerankResult(index=r.index, score=r.relevance_score, text=documents[r.index])
                for r in response.results
            ]

            # Apply min_score limit
            if min_score is not None:
                results = [r for r in results if r.score >= min_score]

            return results
        except Exception as e:
            logger.error(f"Cohere rerank failed: {e}")
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
