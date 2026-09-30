from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy import select, update, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from pydantic import BaseModel

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.knowledge_entry import KnowledgeEntry
from app.models.department import Department
from app.models.audit_event import AuditEvent
from app.core.time_utils import utc_naive
from app.models.knowledge_base import KnowledgeBase
from app.core.permissions import require_document_read
from app.api_compat.utils import (
    format_bytes_to_human,
    get_or_create_department_workspace,
    get_all_department_workspaces,
    get_or_create_default_workspace,
)
from app.api.documents import process_document_background, process_knowledge_background, UPLOAD_DIR
from docx import Document as DocxDocument
import aiofiles
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

ORG_APPROVER_ROLES = {"Admin", "Giám đốc", "Phó giám đốc"}
DEPT_APPROVER_ROLES = {"Admin", "Trưởng phòng"}
ALL_APPROVER_ROLES = ORG_APPROVER_ROLES | DEPT_APPROVER_ROLES

DOC_PENDING_DEPT = "pending"
DOC_PENDING_ORG = "pending_org"
DOC_APPROVED = "approved"

KN_PENDING_DEPT = "pending_dept"
KN_PENDING_ORG = "pending_org"
KN_PENDING_LEGACY = "pending_approval"
KN_APPROVED = "approved"
KN_REJECTED = "rejected"
KN_VISIBILITY_PUBLIC = "public"
KN_VISIBILITY_PRIVATE = "private"


class ApprovalDates(BaseModel):
    reason: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None


def _confirm_dates(item, dates: ApprovalDates | None):
    if dates and dates.effective_from is not None:
        item.effective_from = dates.effective_from
    if dates and "effective_until" in dates.model_fields_set:
        item.effective_until = dates.effective_until
    if item.effective_from is None:
        raise HTTPException(status_code=400, detail="Cần ngày hiệu lực trước khi phê duyệt")
    if item.effective_until and item.effective_until < item.effective_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực phải từ ngày hiệu lực trở đi")


@router.get("/count")
async def pending_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        return {"count": 0}

    if current_user.role == "Admin":
        doc_stmt = select(func.count(Document.id)).where(
            or_(
                Document.approval_status == DOC_PENDING_DEPT,
                Document.approval_status == DOC_PENDING_ORG,
            )
        )
    elif current_user.role == "Trưởng phòng":
        doc_stmt = select(func.count(Document.id)).where(
            Document.approval_status == DOC_PENDING_DEPT,
            Document.department_id == current_user.department_id,
        )
    else:
        # Ban giám đốc chỉ nhận duyệt cấp tổ chức cho tài liệu công khai
        doc_stmt = select(func.count(Document.id)).where(
            Document.approval_status == DOC_PENDING_ORG,
            Document.visibility == KN_VISIBILITY_PUBLIC,
        )
    doc_count = (await db.execute(doc_stmt.where(Document.deleted_at.is_(None)))).scalar() or 0

    if current_user.role == "Admin":
        kn_stmt = select(func.count(KnowledgeEntry.id)).where(
            or_(
                KnowledgeEntry.approval_status.in_([KN_PENDING_DEPT, KN_PENDING_LEGACY]),
                KnowledgeEntry.approval_status == KN_PENDING_ORG,
            )
        )
    elif current_user.role == "Trưởng phòng":
        kn_stmt = select(func.count(KnowledgeEntry.id)).where(
            KnowledgeEntry.approval_status.in_([KN_PENDING_DEPT, KN_PENDING_LEGACY]),
            KnowledgeEntry.department_id == current_user.department_id,
        )
    else:
        kn_stmt = select(func.count(KnowledgeEntry.id)).where(
            KnowledgeEntry.approval_status == KN_PENDING_ORG,
            KnowledgeEntry.visibility == KN_VISIBILITY_PUBLIC,
        )
    kn_count = (await db.execute(kn_stmt.where(KnowledgeEntry.deleted_at.is_(None)))).scalar() or 0

    # Always return last_requester so frontend can show who uploaded
    # even when count increases from 0 → N
    last_requester = None

    # Fetch the most recent pending item (doc or knowledge) scoped by approval stage
    if current_user.role == "Admin":
        latest_doc_result = await db.execute(
            select(User.name, Document.created_at)
            .join(User, Document.uploader_id == User.id)
            .where(
                or_(
                    Document.approval_status == DOC_PENDING_DEPT,
                    Document.approval_status == DOC_PENDING_ORG,
                )
            )
            .where(Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .limit(1)
        )
    elif current_user.role == "Trưởng phòng":
        latest_doc_result = await db.execute(
            select(User.name, Document.created_at)
            .join(User, Document.uploader_id == User.id)
            .where(
                Document.approval_status == DOC_PENDING_DEPT,
                Document.department_id == current_user.department_id,
            )
            .where(Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .limit(1)
        )
    else:
        latest_doc_result = await db.execute(
            select(User.name, Document.created_at)
            .join(User, Document.uploader_id == User.id)
            .where(
                Document.approval_status == DOC_PENDING_ORG,
                Document.visibility == KN_VISIBILITY_PUBLIC,
            )
            .where(Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
            .limit(1)
        )
    doc_row = latest_doc_result.first()

    if current_user.role == "Admin":
        latest_kn_result = await db.execute(
            select(User.name, KnowledgeEntry.created_at)
            .join(User, KnowledgeEntry.owner_id == User.id)
            .where(
                or_(
                    KnowledgeEntry.approval_status.in_([KN_PENDING_DEPT, KN_PENDING_LEGACY]),
                    KnowledgeEntry.approval_status == KN_PENDING_ORG,
                )
            )
            .where(KnowledgeEntry.deleted_at.is_(None))
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(1)
        )
    elif current_user.role == "Trưởng phòng":
        latest_kn_result = await db.execute(
            select(User.name, KnowledgeEntry.created_at)
            .join(User, KnowledgeEntry.owner_id == User.id)
            .where(
                KnowledgeEntry.approval_status.in_([KN_PENDING_DEPT, KN_PENDING_LEGACY]),
                KnowledgeEntry.department_id == current_user.department_id,
            )
            .where(KnowledgeEntry.deleted_at.is_(None))
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(1)
        )
    else:
        latest_kn_result = await db.execute(
            select(User.name, KnowledgeEntry.created_at)
            .join(User, KnowledgeEntry.owner_id == User.id)
            .where(
                KnowledgeEntry.approval_status == KN_PENDING_ORG,
                KnowledgeEntry.visibility == KN_VISIBILITY_PUBLIC,
            )
            .where(KnowledgeEntry.deleted_at.is_(None))
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(1)
        )
    kn_row = latest_kn_result.first()

    if doc_row and kn_row:
        last_requester = doc_row[0] if utc_naive(doc_row[1]) > utc_naive(kn_row[1]) else kn_row[0]
    elif doc_row:
        last_requester = doc_row[0]
    elif kn_row:
        last_requester = kn_row[0]

    total = doc_count + kn_count
    return {"count": total, "last_requester": last_requester}



@router.get("/pending")
async def list_pending(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")

    # Join with User and Department to get names
    if current_user.role == "Admin":
        stmt = (
            select(Document, User.name, Department.name)
            .outerjoin(User, Document.uploader_id == User.id)
            .outerjoin(Department, Document.department_id == Department.id)
            .where(
                or_(
                    Document.approval_status == DOC_PENDING_DEPT,
                    Document.approval_status == DOC_PENDING_ORG,
                )
            )
            .order_by(Document.created_at.desc())
        )
    elif current_user.role == "Trưởng phòng":
        stmt = (
            select(Document, User.name, Department.name)
            .outerjoin(User, Document.uploader_id == User.id)
            .outerjoin(Department, Document.department_id == Department.id)
            .where(
                Document.approval_status == DOC_PENDING_DEPT,
                Document.department_id == current_user.department_id,
            )
            .order_by(Document.created_at.desc())
        )
    else:
        stmt = (
            select(Document, User.name, Department.name)
            .outerjoin(User, Document.uploader_id == User.id)
            .outerjoin(Department, Document.department_id == Department.id)
            .where(
                Document.approval_status == DOC_PENDING_ORG,
                Document.visibility == KN_VISIBILITY_PUBLIC,
            )
            .order_by(Document.created_at.desc())
        )
    result = await db.execute(stmt.where(Document.deleted_at.is_(None)))
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
            "approval_status": doc.approval_status,
            "effective_from": doc.effective_from,
            "effective_until": doc.effective_until,
        })

    # Fetch pending knowledge entries by approval stage
    if current_user.role == "Admin":
        kn_stmt = (
            select(KnowledgeEntry, User.name, Department.name)
            .outerjoin(User, KnowledgeEntry.owner_id == User.id)
            .outerjoin(Department, KnowledgeEntry.department_id == Department.id)
            .where(
                or_(
                    KnowledgeEntry.approval_status.in_([KN_PENDING_DEPT, KN_PENDING_LEGACY]),
                    KnowledgeEntry.approval_status == KN_PENDING_ORG,
                )
            )
            .order_by(KnowledgeEntry.created_at.desc())
        )
    elif current_user.role == "Trưởng phòng":
        kn_stmt = (
            select(KnowledgeEntry, User.name, Department.name)
            .outerjoin(User, KnowledgeEntry.owner_id == User.id)
            .outerjoin(Department, KnowledgeEntry.department_id == Department.id)
            .where(
                KnowledgeEntry.approval_status.in_([KN_PENDING_DEPT, KN_PENDING_LEGACY]),
                KnowledgeEntry.department_id == current_user.department_id,
            )
            .order_by(KnowledgeEntry.created_at.desc())
        )
    else:
        kn_stmt = (
            select(KnowledgeEntry, User.name, Department.name)
            .outerjoin(User, KnowledgeEntry.owner_id == User.id)
            .outerjoin(Department, KnowledgeEntry.department_id == Department.id)
            .where(
                KnowledgeEntry.approval_status == KN_PENDING_ORG,
                KnowledgeEntry.visibility == KN_VISIBILITY_PUBLIC,
            )
            .order_by(KnowledgeEntry.created_at.desc())
        )
    kn_result = await db.execute(kn_stmt.where(KnowledgeEntry.deleted_at.is_(None)))
    kn_rows = kn_result.all()

    knowledge_items = []
    for entry, owner_name, dept_name in kn_rows:
        knowledge_items.append({
            "id": entry.id,
            "title": entry.title,
            "content_text": entry.content_text,
            "category": entry.category,
            "owner": owner_name or "Hệ thống",
            "department": dept_name or "Chung",
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "visibility": entry.visibility,
            "tags": entry.tags,
            "approval_status": entry.approval_status,
            "effective_from": entry.effective_from,
            "effective_until": entry.effective_until,
        })

    return {"documents": docs, "knowledge": knowledge_items}


@router.post("/documents/{doc_id}/approve")
async def approve_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    dates: ApprovalDates | None = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")
    if current_user.role == "Admin" and (not dates or not dates.reason or not dates.reason.strip()):
        raise HTTPException(status_code=400, detail="Admin cần ghi lý do xử lý thay cấp duyệt")

    doc = (await db.execute(select(Document).where(Document.id == doc_id).with_for_update())).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.deleted_at is not None:
        raise HTTPException(status_code=409, detail="Tài liệu đã được đưa vào thùng rác")

    if doc.approval_status == DOC_PENDING_DEPT:
        if current_user.role not in DEPT_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if current_user.role == "Trưởng phòng":
            if current_user.department_id is None or doc.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=403,
                    detail="Không thể phê duyệt tài liệu của phòng ban khác"
                )
        _confirm_dates(doc, dates)
        if (doc.visibility or "internal") == KN_VISIBILITY_PUBLIC:
            db.add(AuditEvent(actor_id=current_user.id, action="approve_department", object_type="document", object_id=doc.id, reason=dates.reason.strip() if dates and dates.reason else None))
            doc.approval_status = DOC_PENDING_ORG
            doc.status = DocumentStatus.PENDING
            await db.commit()
            return {
                "message": "Đã duyệt cấp phòng, đã thông báo tới Ban giám đốc",
                "id": doc_id,
                "processing_started": False,
            }
    elif doc.approval_status == DOC_PENDING_ORG:
        if current_user.role not in ORG_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if (doc.visibility or "internal") != KN_VISIBILITY_PUBLIC:
            raise HTTPException(status_code=400, detail="Tài liệu nội bộ chỉ cần Trưởng phòng phê duyệt")
        _confirm_dates(doc, dates)
    else:
        raise HTTPException(status_code=400, detail="Tài liệu không ở trạng thái chờ duyệt")

    db.add(AuditEvent(actor_id=current_user.id, action="approve_final", object_type="document", object_id=doc.id, reason=dates.reason.strip() if dates and dates.reason else None))
    doc.approval_status = DOC_APPROVED
    doc.approved_by = current_user.id
    doc.approved_at = datetime.utcnow()
    doc.status = DocumentStatus.PROCESSING
    await db.commit()

    # Resolve target workspace: use document's department workspace
    from app.core.config import settings as _settings
    file_path = str(_settings.BASE_DIR / "uploads" / doc.filename)

    if doc.visibility == "public":
        target_ws = await get_or_create_default_workspace(db)
    elif doc.department_id:
        target_ws = await get_or_create_department_workspace(db, doc.department_id)
    else:
        target_ws = await get_or_create_default_workspace(db)

    # Update document's workspace_id to match its department
    doc.workspace_id = target_ws.id
    await db.commit()

    # Trigger background parsing & indexing into department workspace
    background_tasks.add_task(process_document_background, doc.id, file_path, target_ws.id)

    return {"message": "Đã phê duyệt và đang bắt đầu xử lý", "id": doc_id, "processing_started": True}


@router.post("/documents/{doc_id}/reject")
async def reject_document(
    doc_id: int,
    note: str = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")

    doc = (await db.execute(select(Document).where(Document.id == doc_id).with_for_update())).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    rejection_note = (note or "").strip()
    if not rejection_note:
        raise HTTPException(status_code=400, detail="Vui lòng nhập lý do từ chối tài liệu")

    if doc.approval_status == DOC_PENDING_DEPT:
        if current_user.role not in DEPT_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if current_user.role == "Trưởng phòng" and doc.department_id != current_user.department_id:
            raise HTTPException(
                status_code=403,
                detail="Không thể từ chối tài liệu của phòng ban khác"
            )
    elif doc.approval_status == DOC_PENDING_ORG:
        if current_user.role not in ORG_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        # Ban giám đốc: chỉ từ chối ở bước cấp tổ chức của tài liệu công khai
        if (doc.visibility or "internal") != KN_VISIBILITY_PUBLIC:
            raise HTTPException(status_code=400, detail="Chỉ có thể từ chối tài liệu công khai ở bước duyệt cấp tổ chức")
    else:
        raise HTTPException(status_code=400, detail="Tài liệu không ở trạng thái chờ duyệt")

    db.add(AuditEvent(actor_id=current_user.id, action="reject", object_type="document", object_id=doc.id, reason=rejection_note))
    doc.approval_status = "rejected"
    doc.approval_note = rejection_note
    doc.status = DocumentStatus.REJECTED
    await db.commit()
    return {"message": "Đã từ chối tài liệu", "id": doc_id}
@router.get("/documents/{doc_id}/status")
async def get_document_status(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return current processing status of an approved document."""
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")

    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    kb = await db.get(KnowledgeBase, doc.workspace_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_document_read(current_user, doc, kb, allow_owner_pending=True)

    return {
        "id": doc.id,
        "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
        "approval_status": doc.approval_status,
            "effective_from": doc.effective_from,
            "effective_until": doc.effective_until,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


@router.get("/documents/{doc_id}/preview")
async def preview_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")

    doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    kb = await db.get(KnowledgeBase, doc.workspace_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    require_document_read(current_user, doc, kb, allow_owner_pending=True)

    file_path = UPLOAD_DIR / doc.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    ext = doc.file_type.lower()
    text_content = ""

    try:
        if ext == "docx":
            # Quick sync read for docx (safe for small snippets)
            d = DocxDocument(str(file_path))
            # Get first 30 paragraphs
            text_content = "\n".join([p.text for p in d.paragraphs[:30]])
            if len(d.paragraphs) > 30:
                text_content += "\n\n...(Còn tiếp)..."
        elif ext in ("txt", "md"):
            async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
                text_content = await f.read(5000) # first 5k chars
                if len(text_content) == 5000:
                    text_content += "\n\n...(Còn tiếp)..."
        else:
            return {"supported": False, "message": "Preview not supported for this type"}
            
        return {"supported": True, "content": text_content, "file_type": ext}
    except Exception as e:
        logger.error(f"Error previewing file {file_path}: {str(e)}")
        return {"supported": False, "message": f"Error loading preview: {str(e)}"}


@router.get("/knowledge/{entry_id}/preview")
async def preview_pending_knowledge(
    entry_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await db.get(KnowledgeEntry, entry_id)
    if entry is None or entry.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    pending = entry.approval_status in {KN_PENDING_DEPT, KN_PENDING_LEGACY, KN_PENDING_ORG}
    allowed = current_user.role == "Admin"
    if current_user.role == "Trưởng phòng":
        allowed = (entry.approval_status in {KN_PENDING_DEPT, KN_PENDING_LEGACY}
                   and current_user.department_id is not None
                   and current_user.department_id == entry.department_id)
    elif current_user.role in {"Giám đốc", "Phó giám đốc"}:
        allowed = entry.approval_status == KN_PENDING_ORG
    if not pending or not allowed or (entry.visibility or "internal").lower() in {"private", "personal"}:
        raise HTTPException(status_code=403, detail="Permission denied")
    return {"id": entry.id, "title": entry.title, "content_html": entry.content_html,
            "content_text": entry.content_text, "approval_status": entry.approval_status,
            "effective_from": entry.effective_from, "effective_until": entry.effective_until}


@router.post("/knowledge/{entry_id}/approve")
async def approve_knowledge(
    entry_id: int,
    background_tasks: BackgroundTasks,
    dates: ApprovalDates | None = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")
    if current_user.role == "Admin" and (not dates or not dates.reason or not dates.reason.strip()):
        raise HTTPException(status_code=400, detail="Admin cần ghi lý do xử lý thay cấp duyệt")

    entry = (await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id).with_for_update()
    )).scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    if entry.deleted_at is not None:
        raise HTTPException(status_code=409, detail="Tri thức đã được đưa vào thùng rác")

    visibility = (entry.visibility or "internal").lower()
    if visibility in ("personal", KN_VISIBILITY_PRIVATE):
        raise HTTPException(status_code=400, detail="Tri thức cá nhân không cần phê duyệt")

    if entry.approval_status in (KN_PENDING_DEPT, KN_PENDING_LEGACY):
        if current_user.role not in DEPT_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if current_user.role == "Trưởng phòng" and (current_user.department_id is None or entry.department_id != current_user.department_id):
            raise HTTPException(
                status_code=403,
                detail="Không thể phê duyệt tri thức của phòng ban khác"
            )
        _confirm_dates(entry, dates)
        if visibility == KN_VISIBILITY_PUBLIC:
            db.add(AuditEvent(actor_id=current_user.id, action="approve_department", object_type="knowledge", object_id=entry.id, reason=dates.reason.strip() if dates and dates.reason else None))
            entry.approval_status = KN_PENDING_ORG
            entry.status = "Pending"
            await db.commit()
            return {"message": "Đã duyệt cấp phòng, đang chờ duyệt cấp tổ chức", "id": entry_id}
    elif entry.approval_status == KN_PENDING_ORG:
        if current_user.role not in ORG_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if visibility != KN_VISIBILITY_PUBLIC:
            raise HTTPException(status_code=400, detail="Tri thức phòng ban cần Trưởng phòng phê duyệt")
        _confirm_dates(entry, dates)
    else:
        raise HTTPException(status_code=400, detail="Tri thức không ở trạng thái chờ duyệt")

    db.add(AuditEvent(actor_id=current_user.id, action="approve_final", object_type="knowledge", object_id=entry.id, reason=dates.reason.strip() if dates and dates.reason else None))
    entry.approval_status = KN_APPROVED
    entry.approved_by = current_user.id
    entry.approved_at = datetime.utcnow()
    entry.status = "Active"
    entry.ingest_status = "processing"
    await db.commit()

    # Resolve workspace for this knowledge entry
    if entry.visibility == "public":
        target_ws = await get_or_create_default_workspace(db)
    elif entry.department_id:
        target_ws = await get_or_create_department_workspace(db, entry.department_id)
    else:
        target_ws = await get_or_create_default_workspace(db)

    # Trigger background indexing into the department workspace
    background_tasks.add_task(process_knowledge_background, entry_id, target_ws.id)

    return {"message": "Đã phê duyệt tri thức", "id": entry_id}

@router.post("/knowledge/{entry_id}/reject")
async def reject_knowledge(
    entry_id: int,
    note: str = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ALL_APPROVER_ROLES:
        raise HTTPException(status_code=403, detail="Permission denied")

    entry = (await db.execute(
        select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id).with_for_update()
    )).scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    rejection_note = (note or "").strip()
    if not rejection_note:
        raise HTTPException(status_code=400, detail="Vui lòng nhập lý do từ chối tri thức")

    visibility = (entry.visibility or "internal").lower()

    if entry.approval_status in (KN_PENDING_DEPT, KN_PENDING_LEGACY):
        if current_user.role not in DEPT_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if current_user.role == "Trưởng phòng" and entry.department_id != current_user.department_id:
            raise HTTPException(
                status_code=403,
                detail="Không thể từ chối tri thức của phòng ban khác"
            )
    elif entry.approval_status == KN_PENDING_ORG:
        if current_user.role not in ORG_APPROVER_ROLES:
            raise HTTPException(status_code=403, detail="Permission denied")
        if visibility != KN_VISIBILITY_PUBLIC:
            raise HTTPException(status_code=400, detail="Chỉ có thể từ chối tri thức công khai ở bước duyệt cấp tổ chức")
    else:
        raise HTTPException(status_code=400, detail="Tri thức không ở trạng thái chờ duyệt")

    db.add(AuditEvent(actor_id=current_user.id, action="reject", object_type="knowledge", object_id=entry.id, reason=rejection_note))
    entry.approval_status = KN_REJECTED
    entry.approval_note = rejection_note
    entry.status = "Draft"
    await db.commit()
    return {"message": "Đã từ chối tri thức", "id": entry_id}
