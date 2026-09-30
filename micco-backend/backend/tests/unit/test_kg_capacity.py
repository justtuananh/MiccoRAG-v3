"""Capacity limits must bound graph work without crossing KBs or deleting old IDs."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.knowledge_graph_service import KGCapacityExceeded, KnowledgeGraphService
from app.services import knowledge_graph_service as kg_module
from app.api import rag as rag_api


def service(tmp_path, monkeypatch, nodes=None, existing=None):
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    kg = KnowledgeGraphService(77)
    path = tmp_path / "data/lightrag/kb_77"
    path.mkdir(parents=True, exist_ok=True)
    (path / "kv_store_full_docs.json").write_text(json.dumps(existing or {}))
    graph = SimpleNamespace(get_all_nodes=AsyncMock(side_effect=lambda: list(nodes or [])),
                            get_all_edges=AsyncMock(return_value=[]))
    rag = SimpleNamespace(
        full_docs=SimpleNamespace(get_by_id=AsyncMock(return_value=None)),
        chunk_entity_relation_graph=graph,
        ainsert=AsyncMock(),
        adelete_by_doc_id=AsyncMock(),
    )
    kg._get_rag = AsyncMock(return_value=rag)
    return kg, rag


async def test_document_quota_skips_extraction(monkeypatch, tmp_path, caplog):
    kg, rag = service(tmp_path, monkeypatch, existing={"1": {"content": "a"}})
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_DOCUMENTS_PER_KB", 1)
    await kg.ingest("new content", 2)
    rag.ainsert.assert_not_awaited()
    assert "capacity reached" in caplog.text


async def test_parallel_same_kb_ingests_serialize_quota(monkeypatch, tmp_path):
    first, first_rag = service(tmp_path, monkeypatch)
    second, second_rag = service(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_DOCUMENTS_PER_KB", 1)
    full_docs = tmp_path / "data/lightrag/kb_77/kv_store_full_docs.json"

    async def insert(content, ids):
        await asyncio.sleep(0.01)
        full_docs.write_text(json.dumps({ids[0]: {"content": content}}))

    first_rag.ainsert.side_effect = insert
    second_rag.ainsert.side_effect = insert
    await asyncio.gather(first.ingest("one", 1), second.ingest("two", 2))
    assert first_rag.ainsert.await_count + second_rag.ainsert.await_count == 1
    assert len(json.loads(full_docs.read_text())) == 1


async def test_node_quota_skips_extraction(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch, nodes=[{"id": "a"}])
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_NODES_PER_KB", 1)
    await kg.ingest("new content", 2)
    rag.ainsert.assert_not_awaited()


async def test_edge_quota_skips_extraction(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_EDGES_PER_KB", 1)
    rag.chunk_entity_relation_graph.get_all_edges.return_value = [{"source": "a", "target": "b"}]
    await kg.ingest("new content", 2)
    rag.ainsert.assert_not_awaited()


async def test_disk_quota_skips_extraction(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_DISK_BYTES_PER_KB", 1)
    await kg.ingest("new content", 2)
    rag.ainsert.assert_not_awaited()


async def test_process_rss_quota_skips_extraction(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES", 1024)
    monkeypatch.setattr(kg_module, "_process_rss_bytes", lambda: 1024)
    await kg.ingest("new content", 2)
    rag.ainsert.assert_not_awaited()


async def test_crossing_node_cap_rolls_back_new_document(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_NODES_PER_KB", 1)
    rag.chunk_entity_relation_graph.get_all_nodes.side_effect = [[], [{"id": "a"}, {"id": "b"}]]
    with pytest.raises(RuntimeError, match="rolled back document 2"):
        await kg.ingest("new content", 2)
    rag.adelete_by_doc_id.assert_awaited_once_with("2")
    assert kg._chunk_to_doc_map is None


async def test_existing_document_never_rolled_back(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch, existing={"2": {"content": "old"}})
    rag.full_docs.get_by_id.return_value = {"content": "old"}
    await kg.ingest("new content", 2)
    rag.ainsert.assert_not_awaited()
    rag.adelete_by_doc_id.assert_not_awaited()


async def test_graph_query_clamps_internal_call(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch)
    storage = rag.chunk_entity_relation_graph
    storage.get_knowledge_graph = AsyncMock(return_value=SimpleNamespace(nodes=[], edges=[], is_truncated=True))
    monkeypatch.setattr(settings, "NEXUSRAG_KG_GRAPH_MAX_DEPTH", 2)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_GRAPH_MAX_NODES", 3)
    result = await kg.get_graph_data(max_depth=1000, max_nodes=1000000)
    assert result == {"nodes": [], "edges": [], "is_truncated": True}
    assert storage.get_knowledge_graph.await_args.kwargs == {
        "node_label": "*", "max_depth": 2, "max_nodes": 3,
    }


async def test_dense_graph_output_caps_nodes_and_edges(monkeypatch, tmp_path):
    kg, rag = service(tmp_path, monkeypatch)
    storage = rag.chunk_entity_relation_graph
    storage.node_degree = AsyncMock(return_value=1)
    nodes = [SimpleNamespace(id=str(i), properties={}) for i in range(4)]
    edges = [SimpleNamespace(source="0", target="1", properties={}) for _ in range(5)]
    storage.get_knowledge_graph = AsyncMock(return_value=SimpleNamespace(
        nodes=nodes, edges=edges, is_truncated=False,
    ))
    monkeypatch.setattr(settings, "NEXUSRAG_KG_GRAPH_MAX_EDGES", 2)
    result = await kg.get_graph_data(max_nodes=2)
    assert len(result["nodes"]) == 2
    assert len(result["edges"]) == 2
    assert result["is_truncated"] is True


async def test_active_namespace_admission_is_bounded(monkeypatch, tmp_path):
    monkeypatch.setattr(kg_module, "_ACTIVE_KB_NAMESPACES", {41})
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_ACTIVE_KBS_PER_PROCESS", 1)
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    with pytest.raises(RuntimeError, match="active workspace limit"):
        await KnowledgeGraphService(42)._get_rag()


async def test_rss_denies_new_namespace(monkeypatch, tmp_path):
    monkeypatch.setattr(kg_module, "_ACTIVE_KB_NAMESPACES", set())
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    monkeypatch.setattr(settings, "NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES", 1024)
    monkeypatch.setattr(kg_module, "_process_rss_bytes", lambda: 1024)
    with pytest.raises(RuntimeError, match="RSS limit"):
        await KnowledgeGraphService(42)._get_rag()


@pytest.mark.parametrize("route,method", [
    (rag_api.get_kg_graph, "get_graph_data"),
    (rag_api.get_kg_entities, "get_entities"),
    (rag_api.get_kg_relationships, "get_relationships"),
])
async def test_capacity_is_reported_as_503_not_empty_graph(monkeypatch, route, method):
    monkeypatch.setattr(rag_api, "verify_workspace_access", AsyncMock())
    monkeypatch.setattr(rag_api, "get_allowed_document_ids", AsyncMock(return_value=[1]))
    kg = SimpleNamespace(**{method: AsyncMock(side_effect=KGCapacityExceeded("limit"))})
    monkeypatch.setattr(rag_api, "_get_kg_service", AsyncMock(return_value=kg))
    with pytest.raises(HTTPException) as error:
        if route is rag_api.get_kg_graph:
            await route(42, max_depth=1, max_nodes=1, db=object(), current_user=object())
        elif route is rag_api.get_kg_entities:
            await route(42, limit=1, offset=0, db=object(), current_user=object())
        else:
            await route(42, limit=1, db=object(), current_user=object())
    assert error.value.status_code == 503
