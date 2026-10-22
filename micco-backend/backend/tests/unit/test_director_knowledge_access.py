"""Regression coverage for organization-wide read access without write grants."""
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api import workspaces, rag, chat_agent
from app.core.permissions import can_read_document, can_modify_document
from app.schemas.rag import RAGQueryRequest


def user(role):
    return SimpleNamespace(id=7, role=role, department_id=1)


@pytest.mark.parametrize("role", ["Giám đốc", "Phó giám đốc"])
@pytest.mark.parametrize("visibility", ["private", "department", "public"])
def test_directors_read_every_workspace_but_cannot_manage(role, visibility):
    kb = SimpleNamespace(visibility=visibility, department_id=2, owner_id=8)
    assert workspaces._can_access_workspace(user(role), kb)
    assert not workspaces._can_modify_workspace(user(role), kb)
    assert not workspaces._can_delete_workspace(user(role), kb)
    doc = SimpleNamespace(visibility=visibility, department_id=2, uploader_id=8, approval_status="approved")
    assert can_read_document(user(role), doc, kb)
    assert not can_modify_document(user(role), doc, kb)


@pytest.mark.parametrize("role,expected", [
    ("Admin", [1, 2, 3]), ("Giám đốc", [1, 2, 3]),
    ("Phó giám đốc", [1, 2, 3]), ("Nhân viên", [1]),
    ("Trưởng phòng", [1]),
])
@pytest.mark.asyncio
async def test_retrieval_scope_keeps_approval_index_and_workspace_filters(role, expected):
    kb = SimpleNamespace(id=10, visibility="department", department_id=1, owner_id=None)
    docs = [
        SimpleNamespace(id=1, visibility="public", department_id=2, uploader_id=8, approval_status="approved"),
        SimpleNamespace(id=2, visibility="department", department_id=2, uploader_id=8, approval_status="approved"),
        SimpleNamespace(id=3, visibility="private", department_id=2, uploader_id=8, approval_status="approved"),
    ]
    for doc in docs:
        doc.status = "indexed"
        doc.effective_from = date(2020, 1, 1)
        doc.supersedes_document_id = None
    kb_result = SimpleNamespace(scalar_one_or_none=lambda: kb)
    doc_result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: docs))
    db = SimpleNamespace(execute=AsyncMock(side_effect=[kb_result, doc_result]))
    assert await rag.get_allowed_document_ids(db, user(role), 10) == expected


@pytest.mark.parametrize("role", ["Giám đốc", "Phó giám đốc", "Nhân viên"])
@pytest.mark.parametrize("endpoint", ["list_workspaces", "list_workspace_summaries"])
@pytest.mark.asyncio
async def test_workspace_lists_apply_scope_only_to_regular_users(role, endpoint):
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    assert await getattr(workspaces, endpoint)(db=db, current_user=user(role)) == []
    statement = str(db.execute.call_args.args[0])
    assert "knowledge_bases.deleted_at IS NULL" in statement
    assert ("knowledge_bases.owner_id =" in statement) == (role == "Nhân viên")


@pytest.mark.asyncio
async def test_explicit_disallowed_document_does_not_fall_back_to_all():
    request = RAGQueryRequest(question="test", document_ids=[999])
    with patch.object(rag, "verify_workspace_access", AsyncMock()), patch.object(rag, "get_allowed_document_ids", AsyncMock(return_value=[1, 2])), patch.object(rag, "get_rag_service") as factory:
        result = await rag.query_documents(10, request, MagicMock(), user("Giám đốc"))
    assert result.total_chunks == 0
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_query_passes_only_permitted_requested_ids_to_legacy_retrieval():
    service = MagicMock()
    service.query.return_value = SimpleNamespace(query="test", chunks=[], context="")
    request = RAGQueryRequest(question="test", document_ids=[2, 999])
    with patch.object(rag, "verify_workspace_access", AsyncMock(return_value=SimpleNamespace(search_mode="vector_only"))), patch.object(rag, "get_allowed_document_ids", AsyncMock(return_value=[1, 2])), patch.object(rag, "get_rag_service", return_value=service):
        await rag.query_documents(10, request, MagicMock(), user("Giám đốc"))
    assert service.query.call_args.kwargs["document_ids"] == [2]


@pytest.mark.asyncio
async def test_agent_empty_scope_never_calls_retrieval():
    with patch("app.services.rag_service.get_rag_service") as factory:
        assert await chat_agent._execute_search_documents(10, "test", 5, MagicMock(), set(), document_ids=[]) == ("", [], [], [])
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_agent_passes_scope_to_legacy_retrieval():
    service = MagicMock()
    service.query.return_value = SimpleNamespace(chunks=[])
    with patch("app.services.rag_service.get_rag_service", return_value=service):
        await chat_agent._execute_search_documents(10, "test", 5, MagicMock(), set(), document_ids=[1, 2])
    assert service.query.call_args.kwargs["document_ids"] == [1, 2]
