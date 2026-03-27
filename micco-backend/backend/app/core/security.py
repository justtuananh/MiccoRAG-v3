from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.deps import get_db
from app.models.user import User


_BCRYPT_MAX = 72
security = HTTPBearer()


def hash_password(password: str) -> str:
    max_len = settings.COMPAT_BCRYPT_MAX_BYTES or _BCRYPT_MAX
    return _bcrypt.hashpw(password.encode()[:max_len], _bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    max_len = settings.COMPAT_BCRYPT_MAX_BYTES or _BCRYPT_MAX
    return _bcrypt.checkpw(plain_password.encode()[:max_len], hashed_password.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials

    # Dev-mode bypass: VITE_SKIP_AUTH=true sends 'dev-skip' as token
    if token == "dev-skip":
        result = await db.execute(select(User).options(selectinload(User.department)).limit(1))
        user = result.scalar_one_or_none()
        if user:
            return user
        
        # No users in DB — return a transient dummy Admin user
        return User(
            id=1,
            name="System Admin",
            email="admin@example.com",
            hashed_password="dev-mode-transient-auth-skip",
            role="Admin",
            created_at=datetime.utcnow()
        )

    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(
        select(User)
        .options(selectinload(User.department))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

