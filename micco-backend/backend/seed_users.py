"""
Seed script: tạo admin user + 3 user thường vào database.
Chạy: python seed_users.py (từ thư mục backend/)
"""
import asyncio
import sys
import os

# Đảm bảo import đúng module
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.core.database import Base


USERS_TO_SEED = [
    {
        "name": "Admin Hệ Thống",
        "email": "admin@micco.vn",
        "password": os.getenv("SEED_ADMIN_PASSWORD", "Admin_Default_123!"),
        "role": "Admin",
    },
    {
        "name": "Nguyễn Văn A",
        "email": "user1@micco.vn",
        "password": os.getenv("SEED_USER_PASSWORD", "User_Default_123!"),
        "role": "Nhân viên",
    },
    {
        "name": "Trần Thị B",
        "email": "user2@micco.vn",
        "password": os.getenv("SEED_USER_PASSWORD", "User_Default_123!"),
        "role": "Nhân viên",
    },
    {
        "name": "Lê Minh C",
        "email": "user3@micco.vn",
        "password": os.getenv("SEED_USER_PASSWORD", "User_Default_123!"),
        "role": "Nhân viên",
    },
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Tạo bảng nếu chưa có
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        for u in USERS_TO_SEED:
            existing = await db.execute(select(User).where(User.email == u["email"]))
            if existing.scalar_one_or_none() is not None:
                print(f"  [SKIP] {u['email']} đã tồn tại")
                continue

            user = User(
                name=u["name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
            )
            db.add(user)
            await db.commit()
            print(f"  [OK]   {u['email']} ({u['role']}) — tạo thành công")

    await engine.dispose()
    print("\nDone! Seed hoàn tất.")


if __name__ == "__main__":
    asyncio.run(seed())
