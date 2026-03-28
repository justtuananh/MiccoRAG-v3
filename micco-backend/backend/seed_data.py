import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.user import User
from app.models.department import Department
from app.core.database import Base

DEPTS = [
    {"name": "Hành chính Nhân sự", "description": "Quản lý nhân sự và hành chính"},
    {"name": "Phòng Chuyên môn", "description": "Nghiệp vụ chuyên môn"},
    {"name": "Phòng Kỹ thuật", "description": "Hỗ trợ và triển khai kỹ thuật"},
    {"name": "Phòng An toàn", "description": "Quản lý an toàn và bảo mật"},
]

USER_ASSIGNMENTS = {
    "user1@micco.vn": "Hành chính Nhân sự",
    "user2@micco.vn": "Phòng Kỹ thuật",
    "user3@micco.vn": "Phòng Chuyên môn",
}

async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # 1. Seed Departments
        dept_map = {}
        for d in DEPTS:
            existing = await db.execute(select(Department).where(Department.name == d["name"]))
            dept = existing.scalar_one_or_none()
            if not dept:
                dept = Department(name=d["name"], description=d["description"])
                db.add(dept)
                await db.commit()
                await db.refresh(dept)
                print(f"  [OK] Tạo phòng ban: {d['name']}")
            else:
                print(f"  [SKIP] Phòng ban {d['name']} đã tồn tại")
            dept_map[d["name"]] = dept.id

        # 2. Assign Users to Departments
        for email, dept_name in USER_ASSIGNMENTS.items():
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user.department_id = dept_map[dept_name]
                print(f"  [OK] Gán {email} vào {dept_name}")
            else:
                print(f"  [WARN] Không tìm thấy user {email}")
        
        await db.commit()

    await engine.dispose()
    print("\nSeed data hoàn tất.")

if __name__ == "__main__":
    asyncio.run(seed())
