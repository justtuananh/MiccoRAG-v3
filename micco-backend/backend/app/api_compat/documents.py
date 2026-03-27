from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.schemas.compat import LegacyDocumentVersionResponse
from app.api.documents import upload_document
from app.api_compat.utils import (
    format_bytes_to_human,
    get_or_create_default_workspace,
    map_rag_doc_to_legacy,
    workspace_file_path,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("")
async def list_documents(
    search: str | None = Query(None),
    type_filter: str | None = Query(None, alias="type"),
    category: str | None = Query(None),
    department_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = await get_or_create_default_workspace(db)
    stmt = select(Document).where(Document.workspace_id == workspace.id).order_by(Document.created_at.desc())
    docs = (await db.execute(stmt)).scalars().all()

    mapped = [map_rag_doc_to_legacy(doc, owner_name=current_user.name) for doc in docs]

    if search:
        s = search.lower()
        mapped = [d for d in mapped if s in d["name"].lower()]

    if type_filter and type_filter != "All":
        mapped = [d for d in mapped if d["type"] == type_filter.upper()]

    if category and category != "All":
        mapped = [d for d in mapped if d["category"] == category]

    return mapped


@router.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    tags: str | None = Form(None),
    category: str | None = Form(None),
    visibility: str | None = Form("internal"),
    department_id: int | None = Form(None),
    thumbnail: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = await get_or_create_default_workspace(db)

    created: list[dict] = []
    for f in files:
        await upload_document(workspace.id, f, db)

    await db.commit()

    docs = (
        await db.execute(
            select(Document)
            .where(Document.workspace_id == workspace.id)
            .order_by(Document.created_at.desc())
            .limit(len(files))
        )
    ).scalars().all()

    for doc in docs:
        created.append(map_rag_doc_to_legacy(doc, owner_name=current_user.name))

    return list(reversed(created))


@router.get("/{doc_id}")
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return map_rag_doc_to_legacy(doc, owner_name=current_user.name)


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fp = workspace_file_path(doc.filename)
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(fp),
        filename=doc.original_filename,
        media_type="application/octet-stream",
    )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    fp = workspace_file_path(doc.filename)
    if fp.exists():
        os.remove(fp)

    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted successfully"}


@router.get("/{doc_id}/versions", response_model=list[LegacyDocumentVersionResponse])
async def get_document_versions(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return [
        LegacyDocumentVersionResponse(
            id=doc.id,
            document_id=doc.id,
            version_number=1,
            version_label="V 1.0",
            size=format_bytes_to_human(doc.file_size or 0),
            change_note="Auto-mapped from NexusRAG",
            created_by_name="System",
            is_current=True,
            created_at=doc.created_at,
        )
    ]


@router.post("/{doc_id}/versions", response_model=LegacyDocumentVersionResponse)
async def upload_new_version(
    doc_id: int,
    file: UploadFile = File(...),
    change_note: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    old_doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not old_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    workspace = await get_or_create_default_workspace(db)
    await upload_document(workspace.id, file, db)
    await db.commit()

    new_doc = (
        await db.execute(
            select(Document)
            .where(Document.workspace_id == workspace.id)
            .order_by(Document.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if not new_doc:
        raise HTTPException(status_code=500, detail="Failed to create version")

    fp = workspace_file_path(old_doc.filename)
    if fp.exists():
        os.remove(fp)
    await db.delete(old_doc)
    await db.commit()

    return LegacyDocumentVersionResponse(
        id=new_doc.id,
        document_id=new_doc.id,
        version_number=2,
        version_label="V 2.0",
        size=format_bytes_to_human(new_doc.file_size or 0),
        change_note=change_note or "Uploaded new version",
        created_by_name="System",
        is_current=True,
        created_at=new_doc.created_at,
    )


@router.get("/{doc_id}/versions/{version_id}/download")
async def download_version(
    doc_id: int,
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Compatibility fallback: only current file is available.
    _ = version_id
    return await download_document(doc_id, db, current_user)


@router.get("/{doc_id}/thumbnail")
async def get_thumbnail(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
):
    _ = db
    _ = doc_id
    raise HTTPException(status_code=404, detail="Thumbnail not found")
