"""End-to-end integration test of the MiccoRAG-v3 RAG pipeline.

This is the file historically referenced by `.claude/commands/rag-test.md` and
`CLAUDE.md` but that did not exist. It exercises the live backend + Gemini + ChromaDB.
Run via: RUN_INTEGRATION=1 bash harness/run.sh be   (or `... test` with RUN_INTEGRATION=1)
"""
import pytest

pytestmark = pytest.mark.integration


def test_health(api, _backend_up):
    status, body = api("GET", "/health")
    assert status == 200
    assert body.get("status") == "healthy"


def test_ready(api, _backend_up):
    status, _ = api("GET", "/ready")
    assert status == 200


def test_config_status_reports_provider(api, _backend_up):
    status, body = api("GET", "/api/v1/config/status")
    assert status == 200
    assert isinstance(body, dict)
    assert "llm_provider" in body  # gemini / ollama


def test_rag_capabilities(api, _backend_up):
    status, _ = api("GET", "/api/v1/rag/capabilities")
    assert status == 200


def test_workspaces_list_is_array(api, _backend_up):
    status, body = api("GET", "/api/v1/workspaces")
    assert status == 200
    assert isinstance(body, list)


def test_rag_query_returns_retrieval_context(api, workspace_id):
    """POST /rag/query returns a retrieval payload with the documented schema."""
    status, body = api(
        "POST",
        f"/api/v1/rag/query/{workspace_id}",
        body={"question": "Đây là câu kiểm tra tích hợp hệ thống, trả lời ngắn gọn.", "top_k": 3},
        timeout=120,
    )
    assert status == 200, body
    assert isinstance(body, dict)
    # schema từ app/schemas/rag.py::RAGQueryResponse
    assert "total_chunks" in body and isinstance(body["total_chunks"], int)
    assert "chunks" in body and isinstance(body["chunks"], list)
    assert "context" in body
    assert "citations" in body and isinstance(body["citations"], list)
