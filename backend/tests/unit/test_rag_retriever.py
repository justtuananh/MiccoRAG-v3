from app.services.rag.retriever import RetrieverService


def test_retrieve_with_empty_query_returns_empty_list():
    service = RetrieverService()

    result = service.retrieve("", ["a", "b"], top_k=1)

    assert result == []


def test_retrieve_with_query_returns_top_k_candidates():
    service = RetrieverService()

    result = service.retrieve("hello", ["a", "b", "c"], top_k=2)

    assert result == ["a", "b"]
