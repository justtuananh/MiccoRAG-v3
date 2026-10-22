"""Focused regressions for the compatibility upload transaction and authority."""
from datetime import datetime, date
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, UploadFile

from app.api_compat import documents as legacy
from app.models.document import Document


class FakeSession:
    def __init__(self, fail_flush_at=None):
        self.added = []
        self.flush_count = 0
        self.fail_flush_at = fail_flush_at
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flush_count += 1
        if self.flush_count == self.fail_flush_at:
            raise RuntimeError("synthetic database failure")
        for item in self.added:
            if isinstance(item, Document) and item.id is None:
                item.id = 100 + self.flush_count
                item.created_at = datetime(2026, 9, 29)

    async def execute(self, stmt):
        return SimpleNamespace(scalar_one_or_none=lambda: "Phòng A", scalars=lambda: SimpleNamespace(all=lambda: []))


def upload(name, data=b"harmless test data"):
    return UploadFile(filename=name, file=BytesIO(data))


@pytest.fixture
def upload_scope(monkeypatch, tmp_path):
    monkeypatch.setattr(legacy, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(legacy, "THUMBNAIL_DIR", tmp_path / "thumbnails")
    (tmp_path / "thumbnails").mkdir()
    workspace = SimpleNamespace(id=11, visibility="department", department_id=1)
    helper = AsyncMock(return_value=workspace)
    monkeypatch.setattr(legacy, "get_or_create_department_workspace", helper)
    return tmp_path, helper


async def call_upload(files, db, role="Nhân viên", department_id=2):
    user = SimpleNamespace(id=5, name="Test User", role=role, department_id=1)
    return await legacy.upload_documents(
        files=files, tags=None, category=None, visibility="internal", same_name_action=None,
        department_id=department_id, effective_from=date(2026, 1, 1), effective_until=None, thumbnail=None, db=db, current_user=user,
    )


async def test_mixed_file_batch_rejects_before_any_write(upload_scope):
    tmp_path, workspace_helper = upload_scope
    db = FakeSession()
    with pytest.raises(HTTPException) as error:
        await call_upload([upload("good.txt"), upload("bad.exe")], db)
    assert error.value.status_code == 400
    workspace_helper.assert_not_awaited()
    db.commit.assert_not_awaited()
    assert list(tmp_path.glob("*.txt")) == []


async def test_batch_commits_once_and_uses_server_department(upload_scope):
    tmp_path, workspace_helper = upload_scope
    db = FakeSession()
    result = await call_upload([upload("one.txt"), upload("two.md", b"second distinct document")], db, role="Nhân viên", department_id=2)
    assert len(result) == 2
    workspace_helper.assert_awaited_once()
    assert workspace_helper.await_args.args[1] == 1
    assert {doc.department_id for doc in db.added if isinstance(doc, Document)} == {1}
    assert {doc.approval_status for doc in db.added if isinstance(doc, Document)} == {"pending"}
    db.commit.assert_awaited_once()
    assert len(list(tmp_path.glob("*.txt"))) == 1
    assert len(list(tmp_path.glob("*.md"))) == 1


async def test_flush_failure_rolls_back_all_files(upload_scope):
    tmp_path, _ = upload_scope
    db = FakeSession(fail_flush_at=2)
    with pytest.raises(RuntimeError, match="synthetic database failure"):
        await call_upload([upload("one.txt"), upload("two.md", b"second distinct document")], db)
    db.commit.assert_not_awaited()
    db.rollback.assert_awaited_once()
    assert not list(tmp_path.glob("*.txt"))
    assert not list(tmp_path.glob("*.md"))

# Reuse the independent route/SQLite fixture so these assertions exercise the
# ASGI dependency chain, bearer authentication, and committed rows.
from test_fix_crossstack import scoped_api, bearer  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.models import DocumentImage, ChatMessage  # noqa: E402
from sqlalchemy import select  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402


async def test_protected_image_bytes_require_document_and_kb_access(scoped_api, monkeypatch, tmp_path):
    client, db, _ = scoped_api
    monkeypatch.setattr(settings, "BASE_DIR", tmp_path)
    image_path = tmp_path / "data" / "docling" / "kb_12" / "images" / "img-102.png"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic")
    db.add(DocumentImage(document_id=102, image_id="img-102", page_no=1,
                         file_path=str(image_path), caption="fixture",
                         width=1, height=1, mime_type="image/png"))
    await db.commit()
    endpoint = "/api/v1/documents/102/images/img-102/file"
    assert (await client.get(endpoint)).status_code == 401
    assert (await client.get(endpoint, headers=bearer(6))).status_code == 403
    response = await client.get(endpoint, headers=bearer(5))
    assert response.status_code == 200
    assert response.content == image_path.read_bytes()
    assert response.headers["x-content-type-options"] == "nosniff"


async def test_rating_requires_owner_of_assistant_message(scoped_api):
    client, db, _ = scoped_api
    db.add(ChatMessage(workspace_id=10, user_id=5, message_id="rating-fixture",
                       role="assistant", content="fixture answer", sources=[]))
    await db.commit()
    body = {"message_id": "rating-fixture", "source_index": "ab12", "rating": "relevant"}
    assert (await client.post("/api/v1/rag/chat/10/rate", json=body)).status_code == 401
    assert (await client.post("/api/v1/rag/chat/10/rate", json=body, headers=bearer(6))).status_code == 404
    owner = await client.post("/api/v1/rag/chat/10/rate", json=body, headers=bearer(5))
    assert owner.status_code == 200, owner.text
    await db.refresh((await db.execute(select(ChatMessage).where(ChatMessage.message_id == "rating-fixture"))).scalar_one())
    assert (await db.execute(select(ChatMessage.ratings).where(ChatMessage.message_id == "rating-fixture"))).scalar_one() == {"ab12": "relevant"}


async def test_chat_ignores_forged_query_user_id(scoped_api, monkeypatch):
    client, db, _ = scoped_api
    from app.api import rag
    import app.services.llm as llm
    service = MagicMock()
    service.query.return_value = SimpleNamespace(query="fixture", chunks=[], context="")
    monkeypatch.setattr(rag, "get_rag_service", lambda *args, **kwargs: service)
    provider = SimpleNamespace(acomplete=AsyncMock(return_value="Synthetic answer"))
    monkeypatch.setattr(llm, "get_llm_provider", lambda: provider)
    response = await client.post("/api/v1/rag/chat/11?user_id=1",
                                 json={"message": "Synthetic question"}, headers=bearer(5))
    assert response.status_code == 200, response.text
    rows = (await db.execute(select(ChatMessage).where(ChatMessage.workspace_id == 11))).scalars().all()
    assert len(rows) == 2
    assert {row.user_id for row in rows} == {5}


async def test_history_hides_answers_whose_sources_are_no_longer_readable(scoped_api):
    client, db, _ = scoped_api
    db.add(ChatMessage(workspace_id=10, user_id=5, message_id="revoked-answer",
                       role="assistant", content="Formerly authorized private fact",
                       sources=[{"index": "ab12", "document_id": 103}],
                       image_refs=None))
    await db.commit()
    response = await client.get("/api/v1/rag/chat/10/history", headers=bearer(5))
    assert response.status_code == 200, response.text
    assert "Formerly authorized private fact" not in response.text


@pytest.mark.parametrize("path,method,body", [
    ("/api/v1/rag/query/12", "POST", {"question": "synthetic"}),
    ("/api/v1/rag/chat/12", "POST", {"message": "synthetic"}),
    ("/api/v1/rag/chat/12/stream", "POST", {"message": "synthetic"}),
    ("/api/v1/rag/debug-chat/12", "POST", {"message": "synthetic"}),
    ("/api/v1/expert/recommend/12?query=synthetic", "GET", None),
    ("/api/v1/documents/103/download", "GET", None),
    ("/api/documents/103/download", "GET", None),
])
async def test_foreign_private_routes_deny_before_retrieval(scoped_api, path, method, body):
    client, _, vector_calls = scoped_api
    response = await client.request(method, path, json=body, headers=bearer(6))
    assert response.status_code == 403, response.text
    assert "PRIVATE_FIXTURE" not in response.text
    assert vector_calls == []


@pytest.mark.parametrize("uid", [2, 3])
async def test_directors_read_new_private_kb_without_write_right(scoped_api, uid):
    client, db, _ = scoped_api
    from app.models import KnowledgeBase
    db.add(KnowledgeBase(id=88, name="New private fixture", visibility="private", owner_id=5))
    await db.commit()
    assert (await client.get("/api/v1/workspaces/88", headers=bearer(uid))).status_code == 200
    assert (await client.put("/api/v1/workspaces/88", json={"name": "unauthorized"}, headers=bearer(uid))).status_code == 403


async def test_v1_upload_rejects_foreign_private_kb_without_file(scoped_api, monkeypatch, tmp_path):
    client, db, _ = scoped_api
    from app.api import documents
    monkeypatch.setattr(documents, "UPLOAD_DIR", tmp_path)
    response = await client.post("/api/v1/documents/upload/12",
                                 files={"file": ("harmless.txt", b"synthetic", "text/plain")},
                                 data={"effective_from": "2026-01-01"},
                                 headers=bearer(6))
    assert response.status_code == 403, response.text
    assert not list(tmp_path.iterdir())
    assert (await db.execute(select(Document).where(Document.id > 104))).scalars().all() == []


async def test_v1_manager_upload_ignores_forged_department_and_visibility(scoped_api, monkeypatch, tmp_path):
    client, db, _ = scoped_api
    from app.api import documents
    monkeypatch.setattr(documents, "UPLOAD_DIR", tmp_path)
    response = await client.post("/api/v1/documents/upload/11?department_id=2&visibility=public",
                                 files={"file": ("harmless.txt", b"synthetic", "text/plain")},
                                 data={"effective_from": "2026-01-01"},
                                 headers=bearer(4))
    assert response.status_code == 200, response.text
    doc = (await db.execute(select(Document).where(Document.id == response.json()["id"]))).scalar_one()
    assert (doc.department_id, doc.visibility, doc.approval_status) == (1, "department", "approved")
    for path in tmp_path.iterdir():
        path.unlink()


async def test_legacy_query_uses_current_document_filename(scoped_api, monkeypatch):
    client, _, _ = scoped_api
    from app.api import rag
    service = MagicMock()
    service.query.return_value = SimpleNamespace(
        query="synthetic", context="synthetic", chunks=[SimpleNamespace(
            content="synthetic", chunk_id="doc_100_chunk_0", score=0.9,
            metadata={"document_id": 100, "source": "stale-old-name.txt"},
        )],
    )
    monkeypatch.setattr(rag, "get_rag_service", lambda *args, **kwargs: service)
    response = await client.post("/api/v1/rag/query/10", json={"question": "synthetic"}, headers=bearer(5))
    assert response.status_code == 200, response.text
    assert response.json()["chunks"][0]["metadata"]["source"] == "Quy trình 100.txt"


async def test_stream_retrieval_source_uses_current_document_filename(scoped_api, monkeypatch):
    _, db, _ = scoped_api
    from app.api import chat_agent
    import app.services.rag_service as service_module
    service = MagicMock()
    service.query.return_value = SimpleNamespace(chunks=[SimpleNamespace(
        content="synthetic", metadata={"document_id": 100, "source": "stale-old-name.txt"},
    )])
    monkeypatch.setattr(service_module, "get_rag_service", lambda *args, **kwargs: service)
    context, sources, _, _ = await chat_agent._execute_search_documents(
        10, "synthetic", 5, db, set(), document_ids=[100]
    )
    assert sources[0].source_file == "Quy trình 100.txt"
    assert "Quy trình 100.txt" in context
    assert "stale-old-name.txt" not in context
