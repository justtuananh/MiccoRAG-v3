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


@router.get("/departments")
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
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "created_at": d.created_at,
            "user_count": len(d.users),
        }
        for d in depts
    ]


@router.post("/departments", status_code=201)
async def create_department(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tên phòng ban không được trống")

    existing = await db.execute(select(Department).where(Department.name == name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Phòng ban đã tồn tại")

    dept = Department(name=name, description=body.get("description", ""))
    db.add(dept)
    await db.commit()
    await db.refresh(dept)

    return {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
        "created_at": dept.created_at,
        "user_count": 0,
    }


@router.put("/departments/{dept_id}")
async def update_department(
    dept_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Phòng ban không tồn tại")

    if "name" in body:
        new_name = (body["name"] or "").strip()
        if not new_name:
            raise HTTPException(status_code=400, detail="Tên phòng ban không được trống")

        dup = await db.execute(
            select(Department).where(Department.name == new_name, Department.id != dept_id)
        )
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Tên phòng ban đã tồn tại")
        dept.name = new_name

    if "description" in body:
        dept.description = body["description"]

    await db.commit()
    await db.refresh(dept)

    user_count = await db.execute(select(func.count(User.id)).where(User.department_id == dept.id))
    return {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
        "created_at": dept.created_at,
        "user_count": user_count.scalar() or 0,
    }


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
    total_users = await db.execute(select(func.count(User.id)))
    total_docs = await db.execute(select(func.coalesce(func.sum(Document.file_size), 0)))

    return {
        "totalUsers": total_users.scalar() or 0,
        "storageUsed": _fmt_storage(total_docs.scalar() or 0),
        "activeSessions": 0,
        "totalUsersChange": "",
        "storageChange": "",
        "activeSessionsChange": "",
    }


@router.get("/users")
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

    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "department_id": u.department_id,
                "department_name": u.department.name if u.department else None,
                "avatar": u.avatar,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/users", status_code=201)
async def create_user(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    name = (body.get("name") or "").strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Tên phải có ít nhất 2 ký tự")

    email = (body.get("email") or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email không được trống")

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    password = body.get("password") or "123456"
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")

    dept_id = body.get("department_id")
    if not dept_id:
        raise HTTPException(status_code=400, detail="Phòng ban không được để trống")

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=body.get("role", "Nhân viên"),
        department_id=dept_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

    if "name" in body:
        name = body["name"].strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Tên phải có ít nhất 2 ký tự")
        user.name = name

    if "email" in body:
        dup = await db.execute(select(User).where(User.email == body["email"], User.id != user_id))
        if dup.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
        user.email = body["email"]

    if "role" in body:
        user.role = body["role"]

    if "department_id" in body:
        dept_id = body["department_id"]
        if not dept_id:
            raise HTTPException(status_code=400, detail="Phòng ban không được để trống")
        user.department_id = dept_id

    if body.get("password"):
        password = body["password"]
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")
        user.hashed_password = hash_password(password)

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
