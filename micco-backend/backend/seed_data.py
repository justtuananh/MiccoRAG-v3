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
from app.models.knowledge_base import KnowledgeBase
from app.core.database import Base

# Departments hiện tại trong DB
DEPTS = [
    {"name": "Ban Giám đốc", "description": "Ban lãnh đạo công ty"},
    {"name": "Kinh doanh", "description": "Phòng Kinh doanh - Marketing"},
    {"name": "Kế toán", "description": "Phòng Kế toán - Tài chính"},
    {"name": "Kỹ thuật", "description": "Phòng Kỹ thuật - Công nghệ"},
    {"name": "Nhân sự", "description": "Phòng Nhân sự"},
    {"name": "Pháp chế", "description": "Phòng Pháp chế - Hợp đồng"},
]

USER_ASSIGNMENTS = {
    "user1@micco.vn": "Kế toán",
    "user2@micco.vn": "Kỹ thuật",
    "user3@micco.vn": "Kinh doanh",
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

        # 3. Create Workspace cho mỗi Department
        for dept_name, dept_id in dept_map.items():
            existing_kb = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.department_id == dept_id)
            )
            kb = existing_kb.scalar_one_or_none()
            if not kb:
                kb = KnowledgeBase(
                    name=f"KB {dept_name}",
                    description=f"Kiến thức của phòng {dept_name}",
                    department_id=dept_id,
                    search_mode="hybrid",
                )
                db.add(kb)
                await db.commit()
                await db.refresh(kb)
                print(f"  [OK] Tạo workspace cho: {dept_name}")
            else:
                print(f"  [SKIP] Workspace cho {dept_name} đã tồn tại")

        await db.commit()

    await engine.dispose()
    print("\nSeed data hoàn tất.")

if __name__ == "__main__":
    asyncio.run(seed())
