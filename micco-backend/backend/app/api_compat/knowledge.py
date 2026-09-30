from __future__ import annotations
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import can_read_all_knowledge
from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.knowledge_entry import KnowledgeEntry
from app.models.document import Document
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
        "effective_from": entry.effective_from,
        "effective_until": entry.effective_until,
        "deleted_at": entry.deleted_at,
        "supersedes_entry_id": entry.supersedes_entry_id,
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
        .where(KnowledgeEntry.deleted_at.is_(None))
    )

    # RBAC: non-admins only see approved entries in permitted scope + their own
    if can_read_all_knowledge(current_user) and current_user.role != "Admin":
        stmt = stmt.where(or_(
            KnowledgeEntry.approval_status == APPROVAL_APPROVED,
            KnowledgeEntry.owner_id == current_user.id,
        ))
    elif current_user.role != "Admin":
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


@router.get("/trash")
async def list_deleted_knowledge(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(KnowledgeEntry).where(KnowledgeEntry.deleted_at.is_not(None)).options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
    if current_user.role != "Admin": stmt = stmt.where(KnowledgeEntry.owner_id == current_user.id)
    entries = (await db.execute(stmt.order_by(KnowledgeEntry.deleted_at.desc()))).scalars().all()
    return {"items": [_to_response(entry) for entry in entries]}


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

    if not entry or entry.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    if current_user.role != "Admin":
        if entry.owner_id == current_user.id:
            return _to_response(entry)

        vis = _normalize_visibility(entry.visibility)
        if entry.approval_status != APPROVAL_APPROVED:
            raise HTTPException(status_code=403, detail="Permission denied")
        if can_read_all_knowledge(current_user) or vis == VISIBILITY_PUBLIC:
            return _to_response(entry)
        if vis in DEPARTMENT_VISIBILITIES and entry.department_id == current_user.department_id:
            return _to_response(entry)
        if vis == VISIBILITY_PRIVATE:
            raise HTTPException(status_code=403, detail="Permission denied")
        raise HTTPException(status_code=403, detail="Permission denied")

    return _to_response(entry)


async def _queue_index(entry, db, tasks):
    if entry.approval_status != "approved" or tasks is None:
        return
    from app.api_compat.utils import get_or_create_user_workspace, get_or_create_department_workspace, get_or_create_default_workspace, get_all_department_workspaces
    from app.api.documents import process_knowledge_background
    if entry.visibility == "private":
        workspace = await get_or_create_user_workspace(db, entry.owner_id)
    elif entry.visibility == "public":
        workspace = await get_or_create_default_workspace(db)
    elif entry.department_id is not None:
        workspace = await get_or_create_department_workspace(db, entry.department_id)
    else:
        workspace = await get_or_create_default_workspace(db)
    targets = [workspace]
    entry.ingest_status = "processing"
    await db.commit()
    for target in targets:
        tasks.add_task(process_knowledge_background, entry.id, target.id)


@router.post("", status_code=201)
async def create_knowledge(
    body: KnowledgeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    normalized_visibility = _normalize_visibility(body.visibility)
    approval_status = _initial_approval_status(current_user.role, normalized_visibility)
    is_auto_approved = approval_status == APPROVAL_APPROVED
    if body.effective_from is None:
        raise HTTPException(status_code=400, detail="Cần nhập ngày hiệu lực")
    if body.effective_until and body.effective_until < body.effective_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực không hợp lệ")

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
        effective_from=body.effective_from,
        effective_until=body.effective_until,
        approved_by=current_user.id if is_auto_approved else None,
        approved_at=datetime.utcnow() if is_auto_approved else None,
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

    await _queue_index(entry, db, background_tasks)
    return _to_response(entry)


@router.put("/{entry_id}")
async def update_knowledge(
    entry_id: int,
    body: KnowledgeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None,
):
    entry = (
        await db.execute(
            select(KnowledgeEntry)
            .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
            .where(KnowledgeEntry.id == entry_id)
        )
    ).scalar_one_or_none()

    if not entry or entry.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    if entry.owner_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    next_visibility = _normalize_visibility(
        body.visibility if body.visibility is not None else entry.visibility
    )
    if body.effective_from is None and entry.effective_from is None:
        raise HTTPException(status_code=400, detail="Cần nhập ngày hiệu lực")
    next_from = body.effective_from or entry.effective_from
    next_until = body.effective_until if "effective_until" in body.model_fields_set else entry.effective_until
    if next_until and next_until < next_from:
        raise HTTPException(status_code=400, detail="Ngày hết hiệu lực không hợp lệ")
    if entry.approval_status == APPROVAL_APPROVED:
        previous = entry
        # Narrowing visibility immediately restricts existing indexed projections.
        ranks = {"private": 0, "internal": 1, "department": 1, "public": 2}
        if ranks.get(next_visibility, 0) < ranks.get(previous.visibility, 0):
            family = list((await db.execute(select(KnowledgeEntry).where(
                KnowledgeEntry.owner_id == previous.owner_id).with_for_update())).scalars().all())
            by_id = {row.id: row for row in family}
            def root(row):
                seen = set()
                while row.supersedes_entry_id in by_id and row.id not in seen:
                    seen.add(row.id)
                    row = by_id[row.supersedes_entry_id]
                return row.id
            root_id = root(previous)
            narrower_than = [value for value, rank in ranks.items() if rank > ranks[next_visibility]]
            family_ids = []
            department = None if next_visibility == 'private' else (
                previous.department_id if current_user.role == 'Admin' else current_user.department_id)
            for row in family:
                if root(row) == root_id and row.visibility in narrower_than:
                    row.visibility = next_visibility
                    row.department_id = department
                    family_ids.append(row.id)
            await db.execute(update(Document).where(
                Document.knowledge_entry_id.in_(family_ids),Document.visibility.in_(narrower_than),
            ).values(visibility=next_visibility,department_id=department))
        entry = KnowledgeEntry(title=previous.title, content_html=previous.content_html,
            content_text=previous.content_text, category=previous.category, tags=list(previous.tags or []),
            owner_id=previous.owner_id, department_id=previous.department_id,
            visibility=previous.visibility, effective_from=next_from, effective_until=next_until,
            supersedes_entry_id=previous.id, status="Pending", ingest_status="pending")
        db.add(entry)
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

    entry.approved_by = current_user.id if entry.approval_status == APPROVAL_APPROVED else None
    entry.approved_at = datetime.utcnow() if entry.approval_status == APPROVAL_APPROVED else None
    await db.commit()
    await db.refresh(entry)

    entry = (
        await db.execute(
            select(KnowledgeEntry)
            .options(selectinload(KnowledgeEntry.owner), selectinload(KnowledgeEntry.department))
            .where(KnowledgeEntry.id == entry.id)
        )
    ).scalar_one()

    await _queue_index(entry, db, background_tasks)
    return _to_response(entry)


async def _set_knowledge_family_deleted(db, entry, *, restore=False):
    entries = list((await db.execute(select(KnowledgeEntry).with_for_update())).scalars().all())
    by_id = {item.id: item for item in entries}
    def root(item):
        seen = set()
        while item.supersedes_entry_id in by_id and item.id not in seen:
            seen.add(item.id)
            item = by_id[item.supersedes_entry_id]
        return item.id
    target = root(entry)
    stamp = entry.deleted_at if restore else datetime.utcnow()
    ids = []
    for item in entries:
        if root(item) != target:
            continue
        if (restore and item.deleted_at == stamp) or (not restore and item.deleted_at is None):
            item.deleted_at = None if restore else stamp
            ids.append(item.id)
    condition = Document.deleted_at == stamp if restore else Document.deleted_at.is_(None)
    documents = list((await db.execute(select(Document).where(Document.knowledge_entry_id.in_(ids), condition).with_for_update())).scalars().all())
    for doc in documents:
        doc.deleted_at = None if restore else stamp
        if restore: doc.index_cleaned_at = None
    return documents


@router.delete("/{entry_id}", status_code=204)
async def delete_knowledge(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    ).scalar_one_or_none()

    if not entry or entry.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")

    if entry.owner_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    await _set_knowledge_family_deleted(db, entry)
    await db.commit()
    return None


@router.post("/{entry_id}/restore")
async def restore_knowledge(entry_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))).scalar_one_or_none()
    if not entry or entry.deleted_at is None:
        raise HTTPException(status_code=404, detail="Tri thức không có trong thùng rác")
    if entry.owner_id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    if (datetime.utcnow() - entry.deleted_at).days >= 30:
        raise HTTPException(status_code=410, detail="Thời hạn khôi phục đã hết")
    documents = await _set_knowledge_family_deleted(db, entry, restore=True)
    await db.commit()
    from app.services.index_cleanup import queue_restored_documents
    await queue_restored_documents(db, documents, background_tasks)
    return {"id": entry.id, "message": "Đã khôi phục; quyền và hiệu lực được kiểm lại khi truy cập"}


@router.post("/{entry_id}/process")
async def retry_knowledge(entry_id: int, background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id).with_for_update())).scalar_one_or_none()
    if entry is None or entry.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tri thức không tồn tại")
    if current_user.role != "Admin" and entry.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền xử lý tri thức")
    if entry.approval_status != "approved" or entry.effective_from is None:
        raise HTTPException(status_code=400, detail="Tri thức cần được duyệt và xác nhận ngày hiệu lực")
    if entry.ingest_status == "processing":
        raise HTTPException(status_code=409, detail="Tri thức đang được xử lý")
    await _queue_index(entry, db, background_tasks)
    return {"id": entry.id, "message": "Đã lên lịch xử lý tri thức"}
