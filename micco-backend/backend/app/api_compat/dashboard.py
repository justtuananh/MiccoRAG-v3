from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _fmt_storage(total_bytes: int) -> str:
    if total_bytes >= 1024 * 1024 * 1024:
        return f"{total_bytes / (1024 * 1024 * 1024):.1f} GB"
    if total_bytes >= 1024 * 1024:
        return f"{total_bytes / (1024 * 1024):.1f} MB"
    return f"{total_bytes / 1024:.1f} KB"


def dashboard_scope(user):
    return "company" if user.role in {"Admin", "Giám đốc", "Phó giám đốc"} else "department" if user.role == "Trưởng phòng" else "mine"


def _doc_filters(user):
    filters = [Document.deleted_at.is_(None), Document.workspace_id.in_(select(KnowledgeBase.id).where(KnowledgeBase.deleted_at.is_(None)))]
    scope = dashboard_scope(user)
    if scope == "mine":
        filters.append(Document.uploader_id == user.id)
    elif scope == "department":
        filters.append(and_(Document.department_id == user.department_id, Document.department_id.is_not(None)))
    return filters


def _kb_filters(user):
    filters = [KnowledgeBase.deleted_at.is_(None)]
    if dashboard_scope(user) != "company":
        related = select(Document.workspace_id).where(*_doc_filters(user))
        direct = KnowledgeBase.owner_id == user.id if dashboard_scope(user) == "mine" else and_(KnowledgeBase.visibility == "department", KnowledgeBase.department_id == user.department_id, KnowledgeBase.department_id.is_not(None))
        filters.append(or_(direct, KnowledgeBase.id.in_(related)))
    return filters


def month_bounds(now, offset):
    month_index = now.year * 12 + now.month - 1 - offset
    year, month0 = divmod(month_index, 12)
    next_year, next_month0 = divmod(month_index + 1, 12)
    start = datetime(year, month0 + 1, 1, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    end = datetime(next_year, next_month0 + 1, 1, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    return start.astimezone(timezone.utc).replace(tzinfo=None), end.astimezone(timezone.utc).replace(tzinfo=None), start.strftime("%m/%Y")


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scope = dashboard_scope(current_user)
    doc_filter = _doc_filters(current_user)
    kb_filter = _kb_filters(current_user)
    
    total_files = (await db.execute(select(func.count(Document.id)).where(*doc_filter))).scalar() or 0
    total_bytes = (await db.execute(select(func.coalesce(func.sum(Document.file_size), 0)).where(*doc_filter))).scalar() or 0
    user_filters = [User.is_active.is_(True)]
    if scope == "mine": user_filters.append(User.id == current_user.id)
    elif scope == "department": user_filters.append(and_(User.department_id == current_user.department_id, User.department_id.is_not(None)))
    team_members = (await db.execute(select(func.count(User.id)).where(*user_filters))).scalar() or 0
    total_workspaces = (await db.execute(select(func.count(KnowledgeBase.id)).where(*kb_filter))).scalar() or 0
    total_chunks = (await db.execute(select(func.coalesce(func.sum(Document.chunk_count), 0)).where(*doc_filter))).scalar() or 0
    from sqlalchemy import cast, String
    indexed_docs = (await db.execute(
        select(func.count(Document.id)).where(
            cast(Document.status, String).in_(["indexed", "INDEXED"]),
            *doc_filter
        )
    )).scalar() or 0

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = (
        await db.execute(select(func.count(Document.id)).where(Document.created_at >= seven_days_ago, *doc_filter))
    ).scalar() or 0

    approval_rows = (await db.execute(select(Document.approval_status, func.count(Document.id)).where(*doc_filter).group_by(Document.approval_status))).all()
    approval_counts = {state: count for state, count in approval_rows}
    return {
        "approvalCounts": approval_counts,
        "scope": scope,
        "timezone": "Asia/Ho_Chi_Minh",
        "totalFiles": total_files,
        "storageUsed": _fmt_storage(total_bytes),
        "storageBytes": total_bytes,
        "recentUploads": recent_uploads,
        "teamMembers": team_members,
        "totalWorkspaces": total_workspaces,
        "totalChunks": total_chunks,
        "indexedDocs": indexed_docs,
    }


@router.get("/uploads-over-time")
async def get_uploads_over_time(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    rows = []
    for i in range(5, -1, -1):
        start, end, label = month_bounds(now, i)
        count = (await db.execute(select(func.count(Document.id)).where(
            *_doc_filters(current_user), Document.created_at >= start, Document.created_at < end,
        ))).scalar() or 0
        rows.append({"month": label, "uploads": count})

    return rows


@router.get("/storage-by-type")
async def get_storage_by_type(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    type_colors = {
        "PDF": "#6366f1",
        "DOCX": "#8b5cf6",
        "DOC": "#a78bfa",
        "XLSX": "#10b981",
        "PPTX": "#f59e0b",
        "TXT": "#3b82f6",
        "MD": "#06b6d4",
        "PNG": "#ec4899",
        "JPG": "#f43f5e",
        "ZIP": "#eab308",
    }

    result = await db.execute(
        select(Document.file_type, func.coalesce(func.sum(Document.file_size), 0), func.count(Document.id))
        .where(*_doc_filters(current_user))
        .group_by(Document.file_type)
    )

    data = []
    for doc_type, total_bytes, count in result.all():
        type_label = (doc_type or "OTHER").upper().replace(".", "")
        size_mb = round((total_bytes or 0) / (1024 * 1024), 2)
        data.append({
            "type": type_label,
            "size": size_mb,
            "count": count,
            "fill": type_colors.get(type_label, "#6b7280"),
        })

    data.sort(key=lambda x: x["size"], reverse=True)
    return data if data else []


@router.get("/document-status")
async def get_document_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document counts grouped by processing status."""
    status_colors = {
        "indexed": "#10b981",
        "processing": "#f59e0b",
        "pending": "#6b7280",
        "failed": "#ef4444",
        "parsing": "#3b82f6",
        "indexing": "#8b5cf6",
    }

    # If uploader_id filtering is desired:
    doc_filter = _doc_filters(current_user)

    result = await db.execute(
        select(Document.status, func.count(Document.id))
        .where(*doc_filter)
        .group_by(Document.status)
    )

    data = []
    for status, count in result.all():
        status_str = status.value if hasattr(status, 'value') else str(status)
        data.append({
            "status": status_str,
            "count": count,
            "fill": status_colors.get(status_str, "#6b7280"),
        })

    return data


@router.get("/workspace-stats")
async def get_workspace_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get per-workspace document and chunk counts."""
    # Optional: Filter workspace stats by user uploads too?
    # For now, show overall workspace activity but maybe cap it.
    doc_filter = _doc_filters(current_user)

    result = await db.execute(
        select(
            KnowledgeBase.name,
            func.count(Document.id).label("doc_count"),
            func.coalesce(func.sum(Document.chunk_count), 0).label("chunk_count"),
            func.coalesce(func.sum(Document.file_size), 0).label("total_size"),
        )
        .outerjoin(Document, and_(Document.workspace_id == KnowledgeBase.id, *doc_filter))
        .where(*_kb_filters(current_user))
        .group_by(KnowledgeBase.id, KnowledgeBase.name)
        .order_by(func.count(Document.id).desc())
        .limit(10)
    )

    data = []
    for name, doc_count, chunk_count, total_size in result.all():
        data.append({
            "workspace": name,
            "documents": doc_count,
            "chunks": int(chunk_count),
            "sizeMB": round(total_size / (1024 * 1024), 1),
        })

    return data


@router.get("/recent-documents")
async def get_recent_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent 10 documents from MiccoRAG-v2."""
    query = (
        select(Document, KnowledgeBase)
        .join(KnowledgeBase, Document.workspace_id == KnowledgeBase.id)
    )
    query = query.where(*_doc_filters(current_user))
        
    result = await db.execute(
        query.order_by(Document.created_at.desc()).limit(10)
    )

    docs = []
    for row in result.all():
        doc = row[0]
        workspace = row[1]
        from app.core.permissions import can_read_document
        if not can_read_document(current_user, doc, workspace, allow_owner_pending=True):
            continue
        workspace_name = workspace.name
        docs.append({
            "id": doc.id,
            "name": doc.original_filename or doc.filename,
            "type": (doc.file_type or "").upper().replace(".", ""),
            "size": _fmt_storage(doc.file_size or 0),
            "workspace": workspace_name,
            "status": doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
            "chunks": doc.chunk_count,
            "pages": doc.page_count,
            "createdAt": doc.created_at.isoformat() if doc.created_at else None,
        })

    return docs
