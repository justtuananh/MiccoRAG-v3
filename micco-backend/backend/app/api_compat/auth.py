from __future__ import annotations

import os
import uuid
import aiofiles

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.models.department import Department
from app.models.user import User
from app.schemas.compat import (
    DepartmentResponse,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

AVATAR_DIR = settings.BASE_DIR / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5MB
AVATAR_ALLOWED = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.get("/departments", response_model=list[DepartmentResponse])
async def public_departments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).order_by(Department.name))
    return result.scalars().all()


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng. Vui lòng đăng nhập hoặc dùng email khác.",
        )

    name = req.name.strip()
    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên phải có ít nhất 2 ký tự"
        )

    if len(req.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu phải có ít nhất 6 ký tự"
        )

    # Validate department if provided
    if req.department_id is not None:
        dept = await db.execute(select(Department).where(Department.id == req.department_id))
        if dept.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phòng ban không hợp lệ. Vui lòng chọn phòng ban từ danh sách.",
            )

    user = User(
        name=req.name,
        email=req.email,
        hashed_password=hash_password(req.password),
        role="Nhân viên",
        department_id=req.department_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        department_id=current_user.department_id,
        department_name=current_user.department.name if current_user.department else None,
        avatar=current_user.avatar,
    )


from app.schemas.compat import UserUpdateRequest

@router.put("/me", response_model=UserResponse)
async def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.name is not None:
        name = req.name.strip()
        if len(name) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên phải có ít nhất 2 ký tự"
            )
        current_user.name = name

    if req.password is not None:
        if len(req.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu phải có ít nhất 6 ký tự"
            )
        current_user.hashed_password = hash_password(req.password)

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        department_id=current_user.department_id,
        department_name=current_user.department.name if current_user.department else None,
        avatar=current_user.avatar,
    )


# ─── Avatar Upload ─────────────────────────────────────────────────

@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new avatar image for the current user."""
    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Avatar vượt quá giới hạn {AVATAR_MAX_SIZE // (1024*1024)}MB",
        )

    ext = (file.filename or ".jpg").rsplit(".", 1)[-1].lower()
    if f".{ext}" not in AVATAR_ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng avatar không được hỗ trợ. Chỉ chấp nhận: {', '.join(AVATAR_ALLOWED)}",
        )

    # Delete old avatar if exists
    old_avatar = current_user.avatar
    if old_avatar:
        old_path = AVATAR_DIR / old_avatar
        if old_path.exists():
            os.remove(old_path)

    # Save new avatar
    stored_name = f"avatar_{current_user.id}_{uuid.uuid4().hex}.{ext}"
    file_path = AVATAR_DIR / stored_name
    async with aiofiles.open(file_path, "wb") as out:
        await out.write(content)

    current_user.avatar = stored_name
    await db.commit()

    return {"avatar": stored_name}


@router.get("/me/avatar")
async def get_my_avatar(
    current_user: User = Depends(get_current_user),
):
    """Serve the current user's avatar image."""
    if not current_user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    file_path = AVATAR_DIR / current_user.avatar
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Avatar file not found")

    ext = current_user.avatar.rsplit(".", 1)[-1].lower()
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(path=str(file_path), media_type=media_type)


@router.delete("/me/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the current user's avatar."""
    old_avatar = current_user.avatar
    if old_avatar:
        old_path = AVATAR_DIR / old_avatar
        if old_path.exists():
            os.remove(old_path)
        current_user.avatar = None
        await db.commit()

    return {"message": "Đã xóa avatar"}


@router.get("/users/{user_id}/avatar")
async def get_user_avatar(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Serve a user's avatar image (public endpoint)."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or not user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    file_path = AVATAR_DIR / user.avatar
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Avatar file not found")

    ext = user.avatar.rsplit(".", 1)[-1].lower()
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/jpeg")

    return FileResponse(path=str(file_path), media_type=media_type)
