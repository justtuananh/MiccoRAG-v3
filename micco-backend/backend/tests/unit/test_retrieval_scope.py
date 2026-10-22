"""Regression fixtures for document scope and adjacent table retrieval."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.deep_retriever import DeepRetriever
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.models.parsed_document import Citation, EnrichedChunk
from app.services.expert_recommendation import recommend_experts


def retriever(store=None, kg=None):
    return DeepRetriever(9, kg, store or MagicMock(), MagicMock(), reranker=MagicMock())


@pytest.mark.asyncio
async def test_empty_document_scope_skips_vector_and_graph():
    store = MagicMock()
    kg = MagicMock()
    result = await retriever(store, kg).query("approval", document_ids=[])
    assert result.chunks == []
    assert result.knowledge_graph_summary == ""
    store.query.assert_not_called()
    kg.get_relevant_context.assert_not_called()


@pytest.mark.asyncio
async def test_empty_expert_scope_skips_embedding_and_vector():
    assert await recommend_experts(9, "approval", allowed_document_ids=[]) == []


def test_vector_result_outside_scope_is_discarded_even_if_store_ignores_filter():
    store = MagicMock()
    store.query.return_value = {
        "documents": ["secret", "public"], "metadatas": [
            {"document_id": 99, "source": "secret"},
            {"document_id": 22, "source": "public"},
        ], "ids": ["doc_99_chunk_0", "doc_22_chunk_0"],
    }
    found, citations = retriever(store)._vector_query("approval", 5, [22])
    assert [c.content for c in found] == ["public"]
    assert [c.document_id for c in citations] == [22]


def test_rerank_selected_section_adds_whole_adjacent_table_with_citation():
    store = MagicMock()
    # Candidate/rerank selected section 1; the answer is in adjacent table 2.
    store.get_by_ids.return_value = {
        "ids": ["doc_22_chunk_2", "doc_99_chunk_2"],
        "documents": ["Tier C | 20 days | Director", "unauthorized"],
        "metadatas": [
            {"document_id": 22, "chunk_index": 2, "source": "policy", "has_table": True},
            {"document_id": 99, "chunk_index": 2, "source": "private"},
        ],
    }
    chosen = EnrichedChunk("Purchase procedure", 1, "policy", 22)
    chunks, citations = retriever(store)._include_neighbors(
        [chosen], [Citation("policy", 22)], [22]
    )
    assert [c.content for c in chunks] == ["Purchase procedure", "Tier C | 20 days | Director"]
    assert chunks[1].has_table is True
    assert [c.document_id for c in citations] == [22, 22]
    assert "doc_99_chunk_2" not in store.get_by_ids.call_args.args[0]


@pytest.mark.asyncio
async def test_query_recovers_table_dropped_by_reranker():
    store = MagicMock()
    store.query.return_value = {
        "documents": ["Purchase procedure", "Tier C | 20 days | Director"],
        "metadatas": [
            {"document_id": 22, "chunk_index": 1, "source": "policy"},
            {"document_id": 22, "chunk_index": 2, "source": "policy", "has_table": True},
        ],
        "ids": ["doc_22_chunk_1", "doc_22_chunk_2"],
    }
    store.get_by_ids.return_value = {
        "ids": ["doc_22_chunk_2"],
        "documents": ["Tier C | 20 days | Director"],
        "metadatas": [{"document_id": 22, "chunk_index": 2, "source": "policy", "has_table": True}],
    }
    service = retriever(store)
    service.reranker.rerank.return_value = [SimpleNamespace(index=0, score=0.8)]
    result = await service.query("How long is tier C?", mode="vector_only", document_ids=[22], include_images=False)
    assert len(result.chunks) == 2
    assert "Tier C | 20 days | Director" in result.context
    assert [citation.document_id for citation in result.citations] == [22, 22]


@pytest.mark.asyncio
async def test_current_document_filename_replaces_stale_vector_label_without_forbidden_lookup():
    store = MagicMock()
    store.query.return_value = {
        "documents": ["public section", "private section"],
        "metadatas": [
            {"document_id": 22, "chunk_index": 0, "source": "old-prefix-policy.docx", "page_no": 2,
             "heading_path": "Policy > Threshold"},
            {"document_id": 99, "chunk_index": 0, "source": "private.docx"},
        ],
        "ids": ["doc_22_chunk_0", "doc_99_chunk_0"],
    }
    store.get_by_ids.return_value = {"ids": [], "documents": [], "metadatas": []}
    db = MagicMock()
    db.execute = AsyncMock(return_value=SimpleNamespace(all=lambda: [(22, "Quy trình mua sắm vật tư an toàn.docx")]))
    service = DeepRetriever(9, None, store, MagicMock(), db=db, reranker=MagicMock())
    service.reranker.rerank.return_value = [SimpleNamespace(index=0, score=0.8)]

    result = await service.query("procurement", mode="vector_only", document_ids=[22], include_images=False)

    assert len(result.chunks) == 1
    assert result.chunks[0].source_file == "Quy trình mua sắm vật tư an toàn.docx"
    assert result.citations[0].source_file == "Quy trình mua sắm vật tư an toàn.docx"
    assert result.citations[0].page_no == 2
    assert result.citations[0].heading_path == ["Policy", "Threshold"]
    assert "### [1] Quy trình mua sắm vật tư an toàn.docx | p.2 | Policy > Threshold" in result.context
    assert "old-prefix-policy.docx" not in result.context
    statement = str(db.execute.call_args.args[0].compile(compile_kwargs={"literal_binds": True}))
    assert "IN (22)" in statement
    assert "99" not in statement


@pytest.mark.asyncio
async def test_graph_context_rejects_mixed_or_missing_provenance():
    kg = KnowledgeGraphService(9)
    storage = SimpleNamespace(
        get_all_nodes=AsyncMock(return_value=[
            {"id": "APPROVED", "source_id": "a", "description": "safe"},
            {"id": "MIXED", "source_id": "a<SEP>b", "description": "private detail"},
            {"id": "UNKNOWN", "source_id": "missing", "description": "unknown detail"},
        ]),
        get_all_edges=AsyncMock(return_value=[
            {"source": "APPROVED", "target": "MIXED", "source_id": "a", "description": "private edge"},
        ]),
    )
    kg._get_rag = AsyncMock(return_value=SimpleNamespace(chunk_entity_relation_graph=storage))
    kg._get_chunk_to_doc_map = AsyncMock(return_value={"a": "22", "b": "99"})
    context = await kg.get_relevant_context("approved mixed unknown", allowed_doc_ids=[22])
    assert "APPROVED" in context
    assert "private detail" not in context
    assert "unknown detail" not in context
    assert "private edge" not in context
    assert await kg.get_relevant_context("approved", allowed_doc_ids=[]) == ""
    entities = await kg.get_entities(allowed_doc_ids=[22])
    assert [entity["name"] for entity in entities] == ["APPROVED"]
    relationships = await kg.get_relationships(allowed_doc_ids=[22])
    assert relationships == []
    graph = SimpleNamespace(
        nodes=[
            SimpleNamespace(id="APPROVED", properties={"source_id": "a"}),
            SimpleNamespace(id="MIXED", properties={"source_id": "a,b"}),
        ],
        edges=[SimpleNamespace(source="APPROVED", target="MIXED", properties={"source_id": "a"})],
        is_truncated=False,
    )
    storage.get_knowledge_graph = AsyncMock(return_value=graph)
    graph_data = await kg.get_graph_data(allowed_doc_ids=[22])
    assert [node["id"] for node in graph_data["nodes"]] == ["APPROVED"]
    assert graph_data["edges"] == []
    analytics = await kg.get_analytics(allowed_doc_ids=[22])
    assert analytics["entity_count"] == 1
    assert analytics["relationship_count"] == 0
