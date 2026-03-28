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
        "approval_status": entry.approval_status or "pending_approval",
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

    # RBAC: non-admins only see approved entries + their own (regardless of visibility)
    if current_user.role != "Admin":
        stmt = stmt.where(
            or_(
                (KnowledgeEntry.approval_status == "approved") & 
                or_(
                    KnowledgeEntry.visibility == "public",
                    KnowledgeEntry.department_id == current_user.department_id,
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
        vis = entry.visibility or "internal"
        if vis != "public" and entry.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Permission denied")

    return _to_response(entry)


@router.post("", status_code=201)
async def create_knowledge(
    body: KnowledgeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = current_user.role == "Admin"
    entry = KnowledgeEntry(
        title=body.title,
        content_html=body.content_html,
        content_text=body.content_text,
        category=body.category,
        tags=body.tags,
        visibility=body.visibility if body.visibility in ("internal", "public") else "internal",
        status="Pending" if not is_admin else body.status,
        approval_status="approved" if is_admin else "pending_approval",
        owner_id=current_user.id,
        department_id=current_user.department_id,
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

    is_admin = current_user.role == "Admin"
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    
    if not is_admin:
        entry.approval_status = "pending_approval"
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
