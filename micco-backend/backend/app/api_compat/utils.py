from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.models.department import Department


async def get_or_create_default_workspace(db: AsyncSession, *, commit: bool = True) -> KnowledgeBase:
    """Return the global default workspace (for backward compat)."""
    ws_id = settings.COMPAT_DEFAULT_WORKSPACE_ID
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == ws_id, KnowledgeBase.visibility == "public", KnowledgeBase.deleted_at.is_(None)))
    workspace = result.scalar_one_or_none()
    if workspace:
        return workspace

    existing_public = (await db.execute(select(KnowledgeBase).where(
        KnowledgeBase.name == settings.COMPAT_DEFAULT_WORKSPACE_NAME,
        KnowledgeBase.visibility == "public", KnowledgeBase.deleted_at.is_(None)
    ).order_by(KnowledgeBase.id).limit(1))).scalar_one_or_none()
    if existing_public:
        return existing_public

    if not settings.COMPAT_AUTO_CREATE_DEFAULT_WORKSPACE:
        raise RuntimeError("Default workspace does not exist and auto-creation is disabled")

    workspace = KnowledgeBase(
        name=settings.COMPAT_DEFAULT_WORKSPACE_NAME,
        description=settings.COMPAT_DEFAULT_WORKSPACE_DESCRIPTION,
        visibility="public",
        owner_id=None,
    )
    db.add(workspace)
    await db.flush()
    if commit:
        await db.commit()
        await db.refresh(workspace)
    return workspace


async def get_or_create_department_workspace(
    db: AsyncSession,
    department_id: int,
    *, commit: bool = True,
) -> KnowledgeBase:
    """
    Get or create the workspace that belongs to a department.

    Logic: mỗi phòng ban có 1 workspace riêng gắn với department_id.
    Nếu chưa có, tự tạo ra.
    """
    # Find existing workspace for this department
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.department_id == department_id, KnowledgeBase.visibility == "department", KnowledgeBase.deleted_at.is_(None)).order_by(KnowledgeBase.id).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if workspace:
        return workspace

    deleted = (await db.execute(select(KnowledgeBase.id).where(KnowledgeBase.department_id == department_id, KnowledgeBase.deleted_at.is_not(None)))).scalar_one_or_none()
    if deleted is not None:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Kho phòng ban đang ở trong thùng rác; cần khôi phục trước khi gửi tài liệu")

    # Look up department name for a friendly workspace name
    dept_result = await db.execute(
        select(Department.name).where(Department.id == department_id)
    )
    dept_name = dept_result.scalar_one_or_none() or f"Phòng #{department_id}"

    workspace = KnowledgeBase(
        name=f"KB {dept_name}",
        description=f"Kiến thức của phòng {dept_name}",
        department_id=department_id,
        visibility="department",
        owner_id=None,
        search_mode="hybrid",
    )
    db.add(workspace)
    await db.flush()
    if commit:
        await db.commit()
        await db.refresh(workspace)
    return workspace


async def get_all_department_workspaces(db: AsyncSession) -> list[KnowledgeBase]:
    """Return all workspaces that are linked to a department."""
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.department_id.isnot(None), KnowledgeBase.visibility == "department", KnowledgeBase.deleted_at.is_(None))
    )
    return list(result.scalars().all())


async def get_or_create_user_workspace(db: AsyncSession, user_id: int, *, commit: bool = True) -> KnowledgeBase:
    """
    Get or create a personal workspace for a user.

    Personal workspace: owner_id = user_id, visibility = "private"
    Chỉ chính user đó mới truy cập được.
    """
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.owner_id == user_id,
            KnowledgeBase.visibility == "private", KnowledgeBase.deleted_at.is_(None)
        )
    )
    workspace = result.scalars().first()
    if workspace:
        return workspace

    workspace = KnowledgeBase(
        name=f"personal-{user_id}",
        description=f"Không gian cá nhân của người dùng",
        visibility="private",
        owner_id=user_id,
        department_id=None,
    )
    db.add(workspace)
    await db.flush()
    if commit:
        await db.commit()
        await db.refresh(workspace)
    return workspace


def format_bytes_to_human(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def infer_file_type(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].upper() if "." in filename else "FILE"


def map_rag_doc_to_legacy(doc: Any, owner_name: str = "System") -> dict[str, Any]:
    return {
        "id": doc.id,
        "name": doc.original_filename,
        "type": doc.file_type.upper(),
        "category": "Tài liệu",
        "size": format_bytes_to_human(doc.file_size or 0),
        "owner": owner_name,
        "department": None,
        "date": doc.created_at.strftime("%Y-%m-%d") if doc.created_at else "",
        # "date" chỉ có ngày nên frontend không tính được "x giờ trước";
        # trả thêm mốc thời gian đầy đủ (UTC) cho các chỗ cần độ chính xác tới giờ.
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "tags": [],
        "thumbnail": None,
        "visibility": getattr(doc, "visibility", "internal"),
        "approval_status": getattr(doc, "approval_status", "approved"),
        "approval_note": getattr(doc, "approval_note", None),
        "issuer": getattr(doc, "issuer", None),
        "authority_scope": getattr(doc, "authority_scope", None),
        "authority_rank": getattr(doc, "authority_rank", None),
        "authority_verified_at": getattr(doc, "authority_verified_at", None),
        "effective_from": getattr(doc, "effective_from", None),
        "effective_until": getattr(doc, "effective_until", None),
        "deleted_at": getattr(doc, "deleted_at", None),
        "supersedes_document_id": getattr(doc, "supersedes_document_id", None),
        "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
        # Extra RBAC fields for frontend
        "uploader_id": getattr(doc, "uploader_id", None),
        "department_id": getattr(doc, "department_id", None),
        "department_name": None,
    }


def map_rag_doc_to_legacy_with_dept(
    doc: Any,
    owner_name: str = "System",
    dept_name: str | None = None,
) -> dict[str, Any]:
    """Like map_rag_doc_to_legacy but includes department info for the frontend."""
    tags_raw = getattr(doc, "tags", None) or ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    return {
        "id": doc.id,
        "name": doc.original_filename,
        "type": doc.file_type.upper(),
        "category": getattr(doc, "category", None) or "Tài liệu",
        "size": format_bytes_to_human(doc.file_size or 0),
        "owner": owner_name,
        "department": dept_name,
        "date": doc.created_at.strftime("%Y-%m-%d") if doc.created_at else "",
        # Xem chú thích ở map_rag_doc_to_legacy: "date" mất phần giờ.
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "tags": tags,
        "thumbnail": getattr(doc, "thumbnail", None),
        "visibility": getattr(doc, "visibility", "internal"),
        "approval_status": getattr(doc, "approval_status", "approved"),
        "approval_note": getattr(doc, "approval_note", None),
        "issuer": getattr(doc, "issuer", None),
        "authority_scope": getattr(doc, "authority_scope", None),
        "authority_rank": getattr(doc, "authority_rank", None),
        "authority_verified_at": getattr(doc, "authority_verified_at", None),
        "effective_from": getattr(doc, "effective_from", None),
        "effective_until": getattr(doc, "effective_until", None),
        "deleted_at": getattr(doc, "deleted_at", None),
        "supersedes_document_id": getattr(doc, "supersedes_document_id", None),
        "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
        # Extra RBAC fields for frontend
        "uploader_id": getattr(doc, "uploader_id", None),
        "department_id": getattr(doc, "department_id", None),
        "department_name": dept_name,
    }


def workspace_file_path(filename: str) -> Path:
    return settings.BASE_DIR / "uploads" / filename


async def get_current_department_id(db: AsyncSession, user_id: int) -> int | None:
    """Get the department_id for a given user_id."""
    result = await db.execute(select(User.department_id).where(User.id == user_id))
    return result.scalar_one_or_none()
