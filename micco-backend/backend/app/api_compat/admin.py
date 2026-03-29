from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.core.security import get_current_user, hash_password
from app.models.department import Department
from app.models.user import User
from app.models.document import Document
from app.models.system_chat_log import SystemChatLog
from app.schemas.compat import (
    AdminCreateUserRequest,
    AdminUpdateUserRequest,
    AdminUserResponse,
    AdminListUsersResponse,
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentResponse,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _fmt_storage(total_bytes: int) -> str:
    if total_bytes >= 1 << 30:
        return f"{total_bytes / (1 << 30):.1f} GB"
    if total_bytes >= 1 << 20:
        return f"{total_bytes / (1 << 20):.1f} MB"
    return f"{total_bytes / 1024:.1f} KB"


async def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    result = await db.execute(
        select(Department)
        .options(selectinload(Department.users))
        .order_by(Department.name)
    )
    depts = result.scalars().all()
    return [
        DepartmentResponse(
            id=d.id,
            name=d.name,
            description=d.description,
            created_at=d.created_at,
            user_count=len(d.users),
        )
        for d in depts
    ]


@router.post("/departments", status_code=201, response_model=DepartmentResponse)
async def create_department(
    req: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tên phòng ban không được trống")

    existing = await db.execute(select(Department).where(Department.name == name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Phòng ban đã tồn tại")

    dept = Department(name=name, description=req.description or "")
    db.add(dept)
    await db.commit()
    await db.refresh(dept)

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        created_at=dept.created_at,
        user_count=0,
    )


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: int,
    req: DepartmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Phòng ban không tồn tại")

    if req.name is not None:
        new_name = req.name.strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Tên phòng ban không được trống")
        dup = await db.execute(
            select(Department).where(Department.name == new_name, Department.id != dept_id)
        )
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Tên phòng ban đã tồn tại")
        dept.name = new_name

    if req.description is not None:
        dept.description = req.description

    await db.commit()
    await db.refresh(dept)

    user_count = await db.execute(select(func.count(User.id)).where(User.department_id == dept.id))
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        created_at=dept.created_at,
        user_count=user_count.scalar() or 0,
    )


@router.delete("/departments/{dept_id}", status_code=204)
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Phòng ban không tồn tại")

    await db.delete(dept)
    await db.commit()
    return None


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    """Return admin dashboard statistics."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_docs = (await db.execute(select(func.count(Document.id)))).scalar() or 0
    total_bytes = (await db.execute(select(func.coalesce(func.sum(Document.file_size), 0)))).scalar() or 0
    from app.models.knowledge_entry import KnowledgeEntry
    total_knowledge = (await db.execute(select(func.count(KnowledgeEntry.id)))).scalar() or 0
    from app.models.department import Department
    total_departments = (await db.execute(select(func.count(Department.id)))).scalar() or 0

    return {
        "totalUsers": total_users,
        "totalDocuments": total_docs,
        "totalKnowledge": total_knowledge,
        "totalDepartments": total_departments,
        "storageUsed": _fmt_storage(total_bytes),
        "storageBytes": total_bytes,
        "activeSessions": 0,
    }


@router.get("/users", response_model=AdminListUsersResponse)
async def list_users(
    search: str | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    stmt = select(User).options(selectinload(User.department))

    if search:
        stmt = stmt.where(or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))
    if role and role != "All":
        stmt = stmt.where(User.role == role)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = (await db.execute(stmt)).scalars().all()

    return AdminListUsersResponse(
        users=[
            AdminUserResponse(
                id=u.id,
                name=u.name,
                email=u.email,
                role=u.role,
                department_id=u.department_id,
                department_name=u.department.name if u.department else None,
                avatar=u.avatar,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users", status_code=201)
async def create_user(
    req: AdminCreateUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    """Admin creates a new user account."""
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    password = req.password or "123456"
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")

    user = User(
        name=req.name,
        email=req.email,
        hashed_password=hash_password(password),
        role=req.role,
        department_id=req.department_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    req: AdminUpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    """Admin updates an existing user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if req.name is not None:
        name = req.name.strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Tên phải có ít nhất 2 ký tự")
        user.name = name

    if req.email is not None:
        dup = await db.execute(select(User).where(User.email == req.email, User.id != user_id))
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
        user.email = req.email

    if req.role is not None:
        user.role = req.role

    if req.department_id is not None:
        user.department_id = req.department_id

    if req.password is not None:
        if len(req.password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")
        user.hashed_password = hash_password(req.password)

    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    await db.delete(user)
    await db.commit()
    return None


@router.get("/chat-logs")
async def list_chat_logs(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    stmt = select(SystemChatLog)

    if search:
        stmt = stmt.where(
            or_(
                SystemChatLog.question.ilike(f"%{search}%"),
                SystemChatLog.answer.ilike(f"%{search}%"),
                SystemChatLog.ip_address.ilike(f"%{search}%"),
                SystemChatLog.method.ilike(f"%{search}%"),
            )
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar() or 0

    stmt = stmt.order_by(SystemChatLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    logs = (await db.execute(stmt)).scalars().all()

    return {
        "logs": [
            {
                "id": l.id,
                "workspace_id": l.workspace_id,
                "ip_address": l.ip_address,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "response_time": l.response_time,
                "question": l.question,
                "answer": l.answer,
                "method": l.method,
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
