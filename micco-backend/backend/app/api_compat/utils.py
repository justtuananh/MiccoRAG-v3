from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User


async def get_or_create_default_workspace(db: AsyncSession) -> KnowledgeBase:
    """Return the global default workspace (for backward compat)."""
    ws_id = settings.COMPAT_DEFAULT_WORKSPACE_ID
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == ws_id))
    workspace = result.scalar_one_or_none()
    if workspace:
        return workspace

    if not settings.COMPAT_AUTO_CREATE_DEFAULT_WORKSPACE:
        raise RuntimeError("Default workspace does not exist and auto-creation is disabled")

    workspace = KnowledgeBase(
        id=ws_id,
        name=settings.COMPAT_DEFAULT_WORKSPACE_NAME,
        description=settings.COMPAT_DEFAULT_WORKSPACE_DESCRIPTION,
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace


async def get_or_create_user_workspace(db: AsyncSession, user_id: int) -> KnowledgeBase:
    """Create a per-user workspace for AI chat sessions.

    Workspace is named "Không gian cá nhân - {user_name}" but since we don't
    have user_name here, we just use user_id as part of the slug.
    A separate admin-created workspace can be used for shared documents.
    """
    # Try to find existing personal workspace for this user
    # Use a naming convention: "personal-{user_id}"
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.name == f"personal-{user_id}"
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace:
        return workspace

    workspace = KnowledgeBase(
        name=f"personal-{user_id}",
        description=f"Không gian cá nhân của người dùng #{user_id}",
    )
    db.add(workspace)
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
        "tags": [],
        "thumbnail": None,
        "visibility": getattr(doc, "visibility", "internal"),
        "approval_status": getattr(doc, "approval_status", "approved"),
        "approval_note": getattr(doc, "approval_note", None),
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
        "tags": tags,
        "thumbnail": getattr(doc, "thumbnail", None),
        "visibility": getattr(doc, "visibility", "internal"),
        "approval_status": getattr(doc, "approval_status", "approved"),
        "approval_note": getattr(doc, "approval_note", None),
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

