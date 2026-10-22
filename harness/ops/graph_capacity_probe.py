"""Synthetic graph capacity probe; no database, model calls, or service writes.

Run with backend on PYTHONPATH: python harness/ops/graph_capacity_probe.py
The numbers measure the mock 5,000-node graph path only, not production throughput.
"""
import asyncio
import inspect
import json
import tempfile
import time
import tracemalloc
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.rag import get_kg_graph
from app.core.config import settings
from app.services.knowledge_graph_service import KnowledgeGraphService


async def main():
    count = 5000
    nodes = [SimpleNamespace(id=f"node-{i}", properties={"entity_type": "Fixture"})
             for i in range(count)]
    edges = [SimpleNamespace(source=f"node-{i}", target=f"node-{i+1}", properties={})
             for i in range(count - 1)]
    seen = {}

    async def bounded_graph(*, node_label, max_depth, max_nodes):
        seen.update(max_depth=max_depth, max_nodes=max_nodes)
        return SimpleNamespace(nodes=nodes[:max_nodes], edges=edges[:max_nodes-1],
                               is_truncated=max_nodes < count)

    with tempfile.TemporaryDirectory() as dirname:
        original_base = settings.BASE_DIR
        settings.BASE_DIR = Path(dirname)
        try:
            kg = KnowledgeGraphService(991)
            storage = SimpleNamespace(get_knowledge_graph=bounded_graph,
                                      node_degree=AsyncMock(return_value=2),
                                      get_all_nodes=AsyncMock(return_value=nodes),
                                      get_all_edges=AsyncMock(return_value=edges))
            rag = SimpleNamespace(chunk_entity_relation_graph=storage,
                                  ainsert=AsyncMock(),
                                  full_docs=SimpleNamespace(get_by_id=AsyncMock(return_value=None)))
            kg._get_rag = AsyncMock(return_value=rag)
            tracemalloc.start()
            start = time.perf_counter()
            graph = await kg.get_graph_data(max_depth=100000, max_nodes=1000000)
            view_ms = round((time.perf_counter() - start) * 1000, 2)
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            # Existing graph already at quota: extraction must not start.
            previous_cap = settings.NEXUSRAG_KG_MAX_NODES_PER_KB
            settings.NEXUSRAG_KG_MAX_NODES_PER_KB = count
            try:
                await kg.ingest("fixture document", 1)
            finally:
                settings.NEXUSRAG_KG_MAX_NODES_PER_KB = previous_cap
            rag.ainsert.assert_not_awaited()
            api_params = inspect.signature(get_kg_graph).parameters
            def upper(name):
                return next(item.le for item in api_params[name].default.metadata
                            if hasattr(item, "le"))

            api_max_nodes = upper("max_nodes")
            api_max_depth = upper("max_depth")
            assert len(graph["nodes"]) <= settings.NEXUSRAG_KG_GRAPH_MAX_NODES
            assert len(graph["edges"]) <= settings.NEXUSRAG_KG_GRAPH_MAX_NODES - 1
            assert seen == {"max_depth": settings.NEXUSRAG_KG_GRAPH_MAX_DEPTH,
                            "max_nodes": settings.NEXUSRAG_KG_GRAPH_MAX_NODES}
            assert graph["is_truncated"]
            assert api_max_nodes == settings.NEXUSRAG_KG_GRAPH_MAX_NODES
            assert api_max_depth == settings.NEXUSRAG_KG_GRAPH_MAX_DEPTH
            print(json.dumps({
                "fixture_nodes": count, "fixture_edges": count - 1,
                "returned_nodes": len(graph["nodes"]), "returned_edges": len(graph["edges"]),
                "api_max_nodes": api_max_nodes, "api_max_depth": api_max_depth,
                "ingest_at_node_quota_skipped": True,
                "mock_view_ms": view_ms, "mock_view_peak_mib": round(peak_bytes / 1048576, 2),
                "scope": "mock storage only; excludes LightRAG traversal, DB, LLM, and network",
            }, indent=2))
        finally:
            settings.BASE_DIR = original_base


if __name__ == "__main__":
    asyncio.run(main())
