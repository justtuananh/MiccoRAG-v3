from collections.abc import Sequence


class RetrieverService:
    """Simple retriever placeholder with top-k slicing behavior."""

    def retrieve(self, query: str, candidates: Sequence[str], top_k: int = 5) -> list[str]:
        if not query.strip():
            return []
        return list(candidates)[:top_k]
