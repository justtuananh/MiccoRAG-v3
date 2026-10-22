"""Shared KB and document access decisions for both API generations.

Read access is independent of write access: directors can read all KBs, but
only existing owners/managers/admins can change them.
"""
from __future__ import annotations

from fastapi import HTTPException
from datetime import datetime, date
from zoneinfo import ZoneInfo

ORGANIZATION_READER_ROLES = frozenset({"Admin", "Giám đốc", "Phó giám đốc"})


def can_read_all_knowledge(user) -> bool:
    return user.role in ORGANIZATION_READER_ROLES


def can_access_workspace(user, kb) -> bool:
    if getattr(kb, "deleted_at", None) is not None or not getattr(user, "is_active", True):
        return False
    if can_read_all_knowledge(user):
        return True
    if kb.visibility == "public":
        return True
    if kb.visibility == "private":
        return kb.owner_id is not None and kb.owner_id == user.id
    return (
        kb.visibility == "department"
        and kb.department_id is not None
        and kb.department_id == user.department_id
    )


def can_modify_workspace(user, kb) -> bool:
    if user.role == "Admin":
        return True
    if kb.visibility == "private":
        return kb.owner_id is not None and kb.owner_id == user.id
    return (
        user.role == "Trưởng phòng"
        and kb.visibility == "department"
        and kb.department_id is not None
        and kb.department_id == user.department_id
    )


def can_read_document(user, doc, kb, *, allow_owner_pending: bool = False) -> bool:
    if not can_access_workspace(user, kb):
        return False
    if getattr(doc, "deleted_at", None) is not None:
        return False
    is_owner = doc.uploader_id is not None and doc.uploader_id == user.id
    if doc.approval_status != "approved":
        can_review = (
            doc.approval_status == "pending" and user.role == "Trưởng phòng"
            and user.department_id is not None and doc.department_id == user.department_id
        ) or (doc.approval_status == "pending_org" and user.role in {"Giám đốc", "Phó giám đốc"})
        if not ((is_owner or user.role == "Admin" or can_review) and allow_owner_pending):
            return False
    if can_read_all_knowledge(user):
        return True
    if is_owner:
        return True
    if doc.visibility == "private":
        return False
    if doc.visibility == "public":
        return True
    return doc.department_id is not None and doc.department_id == user.department_id


def vietnam_today() -> date:
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()


def is_effective(item, *, on_date: date | None = None) -> bool:
    """Historical rows with unverified dates are never published implicitly."""
    today = on_date or vietnam_today()
    start = getattr(item, "effective_from", None)
    end = getattr(item, "effective_until", None)
    return (getattr(item, "deleted_at", None) is None and start is not None
            and start <= today and (end is None or today <= end))


def can_serve_document(user, doc, kb, *, on_date: date | None = None) -> bool:
    status = getattr(doc.status, "value", doc.status)
    return (can_read_document(user, doc, kb) and str(status).lower() == "indexed"
            and is_effective(doc, on_date=on_date))


def can_serve_knowledge(user, entry, *, on_date: date | None = None) -> bool:
    if not getattr(user, "is_active", True) or not is_effective(entry, on_date=on_date):
        return False
    if entry.approval_status != "approved" or entry.ingest_status not in {"indexed", "completed"}:
        return False
    if entry.owner_id == user.id:
        return True
    if can_read_all_knowledge(user):
        return True
    if entry.visibility == "public":
        return True
    return entry.visibility in {"department", "internal"} and entry.department_id == user.department_id


def can_modify_document(user, doc, kb) -> bool:
    if user.role == "Admin":
        return True
    if not can_access_workspace(user, kb):
        return False
    if doc.uploader_id is not None and doc.uploader_id == user.id:
        return True
    return (
        user.role == "Trưởng phòng"
        and kb.visibility == "department"
        and kb.department_id is not None
        and kb.department_id == user.department_id
        and doc.department_id == kb.department_id
    )


def require_workspace_read(user, kb) -> None:
    if not can_access_workspace(user, kb):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập kho tri thức này")


def require_workspace_write(user, kb) -> None:
    if not can_modify_workspace(user, kb):
        raise HTTPException(status_code=403, detail="Không có quyền sửa kho tri thức này")


def require_document_read(user, doc, kb, *, allow_owner_pending: bool = False) -> None:
    if not can_read_document(user, doc, kb, allow_owner_pending=allow_owner_pending):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu này")


def require_document_write(user, doc, kb) -> None:
    if not can_modify_document(user, doc, kb):
        raise HTTPException(status_code=403, detail="Không có quyền sửa tài liệu này")
