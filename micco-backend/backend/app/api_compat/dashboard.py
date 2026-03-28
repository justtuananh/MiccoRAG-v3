from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select, case, and_
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


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = current_user.role == "Admin"
    
    # Base filters
    doc_filter = [Document.uploader_id == current_user.id] if not is_admin else []
    kb_filter = [] # Workspaces are generally shared but can be filtered if needed
    
    total_files = (await db.execute(select(func.count(Document.id)).where(*doc_filter))).scalar() or 0
    total_bytes = (await db.execute(select(func.coalesce(func.sum(Document.file_size), 0)).where(*doc_filter))).scalar() or 0
    team_members = (await db.execute(select(func.count(User.id)))).scalar() if is_admin else 1
    total_workspaces = (await db.execute(select(func.count(KnowledgeBase.id)))).scalar() or 0
    total_chunks = (await db.execute(select(func.coalesce(func.sum(Document.chunk_count), 0)).where(*doc_filter))).scalar() or 0
    indexed_docs = (await db.execute(
        select(func.count(Document.id)).where(Document.status == DocumentStatus.INDEXED, *doc_filter)
    )).scalar() or 0

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = (
        await db.execute(select(func.count(Document.id)).where(Document.created_at >= seven_days_ago, *doc_filter))
    ).scalar() or 0

    return {
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
    is_admin = current_user.role == "Admin"
    now = datetime.utcnow()
    rows = []

    for i in range(5, -1, -1):
        month_dt = now - timedelta(days=30 * i)
        year, month = month_dt.year, month_dt.month
        month_name = month_dt.strftime("%b")

        where_clause = [
            extract("year", Document.created_at) == year,
            extract("month", Document.created_at) == month,
        ]
        if not is_admin:
            where_clause.append(Document.uploader_id == current_user.id)

        cnt = (
            await db.execute(
                select(func.count(Document.id)).where(*where_clause)
            )
        ).scalar() or 0
        rows.append({"month": month_name, "uploads": cnt})

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
        .where(Document.uploader_id == current_user.id if current_user.role != "Admin" else True)
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
    doc_filter = [Document.uploader_id == current_user.id] if current_user.role != "Admin" else []

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
    doc_filter = [Document.uploader_id == current_user.id] if current_user.role != "Admin" else []

    result = await db.execute(
        select(
            KnowledgeBase.name,
            func.count(Document.id).label("doc_count"),
            func.coalesce(func.sum(Document.chunk_count), 0).label("chunk_count"),
            func.coalesce(func.sum(Document.file_size), 0).label("total_size"),
        )
        .outerjoin(Document, and_(Document.workspace_id == KnowledgeBase.id, *doc_filter))
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
    is_admin = current_user.role == "Admin"
    query = (
        select(Document, KnowledgeBase.name.label("workspace_name"))
        .join(KnowledgeBase, Document.workspace_id == KnowledgeBase.id)
    )
    if not is_admin:
        query = query.where(Document.uploader_id == current_user.id)
        
    result = await db.execute(
        query.order_by(Document.created_at.desc()).limit(10)
    )

    docs = []
    for row in result.all():
        doc = row[0]
        workspace_name = row[1]
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
