"""Version family behavior through the authenticated legacy routes."""
from datetime import date

import pytest
from sqlalchemy import select

from app.models import Document
from app.models.document import DocumentStatus
from app.models.document_version import DocumentVersion
from app.api_compat import documents as legacy_documents
from test_fix_crossstack import scoped_api, bearer


async def test_child_upload_keeps_one_history_and_retries_once(scoped_api, monkeypatch, tmp_path):
    client, db, _ = scoped_api
    monkeypatch.setattr(legacy_documents, "UPLOAD_DIR", tmp_path)
    root = await db.get(Document, 100)
    db.add(DocumentVersion(document_id=root.id, version_number=1, version_label="V 1.0",
                           filename=root.filename, original_filename=root.original_filename,
                           created_by=5, is_current=True))
    await db.commit()

    async def upload(parent, body, key):
        return await client.post(
            f"/api/documents/{parent}/versions",
            files={"file": ("revision.txt", body)},
            data={"effective_from": "2026-01-01"},
            headers={**bearer(5), "Idempotency-Key": key},
        )

    first = await upload(100, b"first revision", "first")
    assert first.status_code == 200, first.text
    first_data = first.json()
    child = (await db.execute(select(Document).where(Document.filename == first_data["filename"]))).scalar_one()
    second = await upload(child.id, b"second revision", "second")
    assert second.status_code == 200, second.text
    assert [first_data["version_number"], second.json()["version_number"]] == [2, 3]
    assert second.json()["document_id"] == root.id
    assert (await upload(child.id, b"second revision", "second")).json() == second.json()
    assert (await upload(child.id, b"changed revision", "second")).status_code == 409
    assert (await upload(root.id, b"second revision", "second")).status_code == 409
    assert (await upload(child.id, b"third revision", "x" * 129)).status_code == 422
    assert len(list(tmp_path.iterdir())) == 2
    rows = (await db.execute(select(DocumentVersion).where(DocumentVersion.document_id == root.id)
                             .order_by(DocumentVersion.version_number))).scalars().all()
    assert [row.version_number for row in rows] == [1, 2, 3]
    assert rows[2].supersedes_version_id == rows[1].id
    listing = await client.get(f"/api/documents/{child.id}/versions", headers=bearer(5))
    assert listing.status_code == 200, listing.text
    assert [row["version_number"] for row in listing.json()] == [3, 2, 1]


async def test_restore_rejects_hash_reuploaded_while_family_deleted(scoped_api):
    client, db, _ = scoped_api
    root = await db.get(Document, 100)
    root.content_hash = "a" * 64
    await db.commit()
    assert (await client.delete("/api/documents/100", headers=bearer(5))).status_code == 200
    db.add(Document(workspace_id=10, filename="replacement.txt", original_filename="replacement.txt",
                    file_type="txt", file_size=1, status=DocumentStatus.INDEXED,
                    uploader_id=5, department_id=1, visibility="public", approval_status="approved",
                    effective_from=date(2026, 1, 1), content_hash="a" * 64))
    await db.commit()
    result = await client.post("/api/documents/100/restore", headers=bearer(5))
    assert result.status_code == 409, result.text
    await db.refresh(root)
    assert root.deleted_at is not None
