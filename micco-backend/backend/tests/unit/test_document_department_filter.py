"""B03: selected department intersects existing access, approval and trash scope."""
from datetime import datetime

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api_compat.documents import router
from app.core.config import settings
from app.core.database import Base
from app.core.deps import get_db
from app.core.security import create_access_token
from app.models import Department, Document, KnowledgeBase, User
from app.models.document import DocumentStatus


@pytest_asyncio.fixture
async def documents_api(monkeypatch):
    """Real SQL and auth in an isolated DB; no production data or providers."""
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "b03-isolated-test-key-never-deployed")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            db.add_all([Department(id=3, name="Kỹ thuật"), Department(id=6, name="Ban Giám đốc")])
            for uid, role, dept in [
                (1, "Nhân viên", 3), (2, "Trưởng phòng", 3),
                (3, "Admin", None), (4, "Giám đốc", 6),
                (5, "Phó giám đốc", 6), (6, "Nhân viên", 6),
                (7, "Nhân viên", None),
            ]:
                db.add(User(id=uid, name=f"B03-{uid}", email=f"b03-{uid}@fixture.test",
                            hashed_password="unused", role=role, department_id=dept))
            db.add_all([
                KnowledgeBase(id=10, name="Public", visibility="public"),
                KnowledgeBase(id=11, name="Tech", visibility="department", department_id=3),
                KnowledgeBase(id=12, name="Board", visibility="department", department_id=6),
                KnowledgeBase(id=13, name="Other private", visibility="private", owner_id=6),
                KnowledgeBase(id=14, name="Own private", visibility="private", owner_id=1),
            ])
            # id, workspace, department, visibility, owner, approval, deleted
            for did, wid, dept, vis, owner, approval, deleted in [
                (51, 11, 3, "internal", 1, "approved", False),
                (52, 10, 6, "public", 6, "approved", False),
                (53, 12, 6, "internal", 6, "approved", False),
                (54, 10, 6, "private", 6, "approved", False),
                (55, 10, 6, "public", 6, "pending", False),
                (56, 10, 6, "public", 6, "rejected", False),
                (57, 13, 6, "public", 6, "approved", False),
                (58, 11, 3, "internal", 1, "pending", False),
                (59, 14, None, "private", 1, "approved", False),
                (60, 10, 6, "public", 1, "approved", True),
                (61, 11, 3, "internal", 1, "approved", True),
                (62, 10, 6, "public", 6, "approved", True),
            ]:
                db.add(Document(
                    id=did, workspace_id=wid, department_id=dept, visibility=vis,
                    uploader_id=owner, approval_status=approval,
                    deleted_at=datetime(2026, 10, 22) if deleted else None,
                    filename=f"{did}.txt", original_filename=f"B03-{did}.txt",
                    file_type="txt", file_size=10, status=DocumentStatus.INDEXED,
                ))
            await db.commit()

            async def database():
                yield db

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_db] = database
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://b03-fixture"
            ) as client:
                yield client
    finally:
        await engine.dispose()


@pytest.mark.parametrize("uid,department,expected", [
    (1, None, {51, 52, 58, 59}),  # All preserves own pending and personal docs.
    (1, 3, {51, 58}),
    (1, 6, {52}),  # Cross-department public only; never Tech DOC51.
    (1, 999, set()),
    (2, None, {51, 52}),
    (2, 3, {51}),
    (2, 6, {52}),
    (3, 3, {51}),
    (3, 6, {52, 53, 54, 56, 57}),  # Admin keeps existing rejected visibility.
    (4, 3, {51}),
    (4, 6, {52, 53, 54, 57}),
    (5, 6, {52, 53, 54, 57}),
    (6, 3, set()),
    (6, 6, {52, 53, 54, 55, 57}),
    (7, None, {52}),
    (7, 3, set()),
    (7, 6, {52}),
])
async def test_department_filter_intersects_permissions(documents_api, uid, department, expected):
    params = {} if department is None else {"department_id": department}
    response = await documents_api.get(
        "/api/documents", params=params,
        headers={"Authorization": "Bearer " + create_access_token({"sub": uid})},
    )
    assert response.status_code == 200, response.text
    assert {item["id"] for item in response.json()} == expected


@pytest.mark.parametrize("uid,department,expected", [
    (1, None, {60, 61}), (1, 3, {61}), (1, 6, {60}),
    (2, 6, set()), (3, 6, {60, 62}), (4, 6, set()),
])
async def test_department_filter_intersects_trash_ownership(documents_api, uid, department, expected):
    params = {"include_deleted": "true"}
    if department is not None:
        params["department_id"] = department
    response = await documents_api.get(
        "/api/documents", params=params,
        headers={"Authorization": "Bearer " + create_access_token({"sub": uid})},
    )
    assert response.status_code == 200, response.text
    assert {item["id"] for item in response.json()} == expected
