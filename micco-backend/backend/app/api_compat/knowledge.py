from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.knowledge_entry import KnowledgeEntry
from app.models.user import User
from app.schemas.compat import KnowledgeCreateRequest, KnowledgeUpdateRequest

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

ORG_APPROVER_ROLES = {"Admin", "Giám đốc", "Phó giám đốc"}
DEPT_APPROVER_ROLES = {"Admin", "Trưởng phòng"}

APPROVAL_PENDING_DEPT = "pending_dept"
APPROVAL_PENDING_ORG = "pending_org"
APPROVAL_APPROVED = "approved"
VISIBILITY_PRIVATE = "private"
VISIBILITY_PUBLIC = "public"
DEPARTMENT_VISIBILITIES = {"internal", "department"}


def _normalize_visibility(raw_visibility: str | None) -> str:
    visibility = (raw_visibility or "internal").lower()
    if visibility in ("personal", "private"):
        return VISIBILITY_PRIVATE
    if visibility in ("internal", "department", VISIBILITY_PUBLIC):
        return visibility
    return "internal"


def _initial_approval_status(role: str, visibility: str) -> str:
    is_org_approver = role in ORG_APPROVER_ROLES
    is_dept_approver = role in DEPT_APPROVER_ROLES

    if visibility == VISIBILITY_PRIVATE:
        return APPROVAL_APPROVED

    if visibility == VISIBILITY_PUBLIC:
        if is_org_approver:
            return APPROVAL_APPROVED
        if is_dept_approver:
            return APPROVAL_PENDING_ORG
        return APPROVAL_PENDING_DEPT

    if is_org_approver or is_dept_approver:
        return APPROVAL_APPROVED
    return APPROVAL_PENDING_DEPT


def _to_response(entry: KnowledgeEntry) -> dict:
    return {
        "id": entry.id,
        "title": entry.title,
        "content_html": entry.content_html,
        "content_text": entry.content_text,
        "category": entry.category,
        "tags": entry.tags or [],
        "owner": entry.owner.name if entry.owner else "Unknown",
        "department": entry.department.name if entry.department else None,
        "visibility": entry.visibility or "internal",
        "approval_status": entry.approval_status or APPROVAL_PENDING_DEPT,
        "approval_note": entry.approval_note,
        "status": entry.status,
        "ingest_status": entry.ingest_status,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


@router.get("")
async def list_knowledge(
    search: str | None = Query(None),
    category: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(KnowledgeEntry)
        .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
    )

    # RBAC: non-admins only see approved entries in permitted scope + their own
    if current_user.role != "Admin":
        stmt = stmt.where(
            or_(
                (KnowledgeEntry.approval_status == APPROVAL_APPROVED) &
                or_(
                    KnowledgeEntry.visibility == VISIBILITY_PUBLIC,
                    (KnowledgeEntry.visibility.in_(list(DEPARTMENT_VISIBILITIES))) &
                    (KnowledgeEntry.department_id == current_user.department_id),
                ),
                KnowledgeEntry.owner_id == current_user.id
            )
        )

    if search:
        stmt = stmt.where(
            or_(
                KnowledgeEntry.title.ilike(f"%{search}%"),
                KnowledgeEntry.content_text.ilike(f"%{search}%"),
            )
        )
    if category:
        stmt = stmt.where(KnowledgeEntry.category == category)
    if status:
        stmt = stmt.where(KnowledgeEntry.status == status)

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar() or 0

    rows = (
        await db.execute(
            stmt.order_by(KnowledgeEntry.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return {
        "items": [_to_response(e) for e in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{entry_id}")
async def get_knowledge(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        await db.execute(
            select(KnowledgeEntry)
            .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
            .where(KnowledgeEntry.id == entry_id)
        )
    ).scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    if current_user.role != "Admin":
        if entry.owner_id == current_user.id:
            return _to_response(entry)

        vis = _normalize_visibility(entry.visibility)
        if entry.approval_status != APPROVAL_APPROVED:
            raise HTTPException(status_code=403, detail="Permission denied")
        if vis == VISIBILITY_PUBLIC:
            return _to_response(entry)
        if vis in DEPARTMENT_VISIBILITIES and entry.department_id == current_user.department_id:
            return _to_response(entry)
        if vis == VISIBILITY_PRIVATE:
            raise HTTPException(status_code=403, detail="Permission denied")
        raise HTTPException(status_code=403, detail="Permission denied")

    return _to_response(entry)


@router.post("", status_code=201)
async def create_knowledge(
    body: KnowledgeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    normalized_visibility = _normalize_visibility(body.visibility)
    approval_status = _initial_approval_status(current_user.role, normalized_visibility)
    is_auto_approved = approval_status == APPROVAL_APPROVED

    entry = KnowledgeEntry(
        title=body.title,
        content_html=body.content_html,
        content_text=body.content_text,
        category=body.category,
        tags=body.tags,
        visibility=normalized_visibility,
        status=body.status if is_auto_approved else "Pending",
        approval_status=approval_status,
        owner_id=current_user.id,
        department_id=None if normalized_visibility == VISIBILITY_PRIVATE else current_user.department_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    entry = (
        await db.execute(
            select(KnowledgeEntry)
            .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
            .where(KnowledgeEntry.id == entry.id)
        )
    ).scalar_one()

    return _to_response(entry)


@router.put("/{entry_id}")
async def update_knowledge(
    entry_id: int,
    body: KnowledgeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        await db.execute(
            select(KnowledgeEntry)
            .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
            .where(KnowledgeEntry.id == entry_id)
        )
    ).scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    if entry.owner_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    next_visibility = _normalize_visibility(
        body.visibility if body.visibility is not None else entry.visibility
    )
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    entry.visibility = next_visibility
    if next_visibility == VISIBILITY_PRIVATE:
        entry.department_id = None
    elif current_user.role != "Admin":
        entry.department_id = current_user.department_id
    entry.approval_status = _initial_approval_status(current_user.role, next_visibility)
    if entry.approval_status != APPROVAL_APPROVED:
        entry.status = "Pending"

    await db.commit()
    await db.refresh(entry)

    entry = (
        await db.execute(
            select(KnowledgeEntry)
            .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
            .where(KnowledgeEntry.id == entry.id)
        )
    ).scalar_one()

    return _to_response(entry)


@router.delete("/{entry_id}", status_code=204)
async def delete_knowledge(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    ).scalar_one_or_none()

    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    if entry.owner_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await db.delete(entry)
    await db.commit()
    return None
