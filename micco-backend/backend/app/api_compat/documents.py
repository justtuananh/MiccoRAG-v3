from __future__ import annotations

import os
import uuid
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
    
    # Base query: approved documents only, unless you are uploader
    stmt = select(Document).where(Document.workspace_id == workspace.id)
    
    # Filter by approval status: non-admins only see approved ones
    if current_user.role not in ("Admin", "Trưởng phòng"):
        stmt = stmt.where(
            (Document.approval_status == "approved") | 
            (Document.uploader_id == current_user.id)
        )
        # Filter by visibility
        stmt = stmt.where(
            (Document.visibility == "public") |
            (Document.department_id == current_user.department_id) |
            (Document.uploader_id == current_user.id)
        )
    
    stmt = stmt.order_by(Document.created_at.desc())
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

    # Admins and Managers get auto-approved; regular users need approval
    is_admin = current_user.role in ("Admin", "Trưởng phòng")
    doc_approval_status = "approved" if is_admin else "pending"
    effective_dept_id = department_id if department_id is not None else current_user.department_id

    for f in files:
        content = await f.read()
        ext = Path(f.filename).suffix.lower() if f.filename else ""
        filename = f"{uuid.uuid4()}{ext}"

        doc = Document(
            workspace_id=workspace.id,
            filename=filename,
            original_filename=f.filename,
            file_type=ext[1:] if ext else "file",
            file_size=len(content),
            status=DocumentStatus.PENDING,
            uploader_id=current_user.id,
            department_id=effective_dept_id,
            visibility=visibility or "internal",
            approval_status=doc_approval_status,
        )
        db.add(doc)

    await db.commit()

    docs = (
        await db.execute(
            select(Document)
            .where(Document.workspace_id == workspace.id)
            .order_by(Document.created_at.desc())
            .limit(len(files))
        )
    ).scalars().all()

    created = [map_rag_doc_to_legacy(doc, owner_name=current_user.name) for doc in reversed(docs)]
    return created


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
    is_admin = current_user.role in ("Admin", "Trưởng phòng")

    content = await file.read()
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    filename = f"{uuid.uuid4()}{ext}"

    new_doc = Document(
        workspace_id=workspace.id,
        filename=filename,
        original_filename=file.filename,
        file_type=ext[1:] if ext else "file",
        file_size=len(content),
        status=DocumentStatus.PENDING,
        uploader_id=current_user.id,
        department_id=current_user.department_id,
        visibility=old_doc.visibility,
        approval_status="approved" if is_admin else old_doc.approval_status,
    )
    db.add(new_doc)
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
