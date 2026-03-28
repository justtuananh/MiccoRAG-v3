from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.department import Department
from app.api_compat.utils import format_bytes_to_human
from app.api.documents import process_document_background

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


@router.get("/count")
async def pending_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("Admin", "Trưởng phòng"):
        return {"count": 0}
    
    stmt = select(func.count(Document.id)).where(Document.approval_status == "pending")
    count = (await db.execute(stmt)).scalar() or 0
    return {"count": count}


@router.get("/pending")
async def list_pending(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("Admin", "Trưởng phòng"):
        return {"documents": [], "knowledge": []}

    # Join with User and Department to get names
    stmt = (
        select(Document, User.name, Department.name)
        .outerjoin(User, Document.uploader_id == User.id)
        .outerjoin(Department, Document.department_id == Department.id)
        .where(Document.approval_status == "pending")
        .order_by(Document.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    docs = []
    for doc, uploader_name, dept_name in rows:
        docs.append({
            "id": doc.id,
            "name": doc.original_filename,
            "category": "Tài liệu",
            "owner": uploader_name or "Hệ thống",
            "department": dept_name or "Chung",
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "size": format_bytes_to_human(doc.file_size or 0),
            "visibility": doc.visibility,
            "file_type": doc.file_type.lower(),
        })

    return {"documents": docs, "knowledge": []}


@router.post("/documents/{doc_id}/approve")
async def approve_document(
    doc_id: int, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("Admin", "Trưởng phòng"):
        raise HTTPException(status_code=403, detail="Permission denied")

    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.approval_status = "approved"
    doc.status = DocumentStatus.PROCESSING # Set to processing as we start indexing
    await db.commit()

    # Trigger background parsing & indexing (NexusRAG style)
    from app.core.config import settings
    file_path = str(settings.BASE_DIR / "uploads" / doc.filename)
    background_tasks.add_task(process_document_background, doc.id, file_path, doc.workspace_id)
    
    return {"message": "Đã phê duyệt và đang bắt đầu xử lý", "id": doc_id}


@router.post("/documents/{doc_id}/reject")
async def reject_document(
    doc_id: int, 
    note: str = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("Admin", "Trưởng phòng"):
        raise HTTPException(status_code=403, detail="Permission denied")

    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.approval_status = "rejected"
    doc.approval_note = note
    await db.commit()
    
    return {"message": "Đã từ chối", "id": doc_id}
