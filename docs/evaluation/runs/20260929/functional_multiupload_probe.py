"""Isolated multi-upload behavior with async SQLite and temp upload directory."""
import asyncio
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.database import Base
import app.models
from app.models import User, Department, KnowledgeBase, Document, DocumentVersion
from app.api_compat import documents as compat


def file(name, content=b"fixture"):
    return UploadFile(file=io.BytesIO(content), filename=name)


async def main():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    with TemporaryDirectory(prefix="micco-multiupload-") as td:
        tmp = Path(td)
        async with maker() as db:
            dept=Department(id=1,name="Fixture A")
            actor=User(id=1,name="Fixture Staff",email="multi@fixture.test",hashed_password="x",role="Nhân viên",department_id=1)
            kb=KnowledgeBase(id=1,name="Fixture KB",visibility="department",department_id=1)
            db.add_all([dept,actor,kb]); await db.commit()
            async def upload(files):
                return await compat.upload_documents(files=files,tags=None,category=None,visibility="internal",
                    department_id=None,thumbnail=None,db=db,current_user=actor)
            with patch.object(compat,"UPLOAD_DIR",tmp), patch.object(compat,"THUMBNAIL_DIR",tmp), \
                 patch.object(compat,"get_or_create_department_workspace",new=AsyncMock(return_value=kb)):
                try:
                    await upload([file("valid.txt",b"GOOD-ONE"),file("invalid.exe",b"BAD-TWO")])
                    mixed={"status":200}
                except HTTPException as exc:
                    mixed={"status":exc.status_code,"detail":exc.detail}
                docs=(await db.execute(select(Document).order_by(Document.id))).scalars().all()
                versions=(await db.execute(select(DocumentVersion))).scalars().all()
                mixed.update({"documents_after":len(docs),"versions_after":len(versions),
                    "saved_names":[d.original_filename for d in docs],
                    "saved_file_count":len([p for p in tmp.iterdir() if p.is_file()])})
                first=await upload([file("same.txt",b"SAME")])
                second=await upload([file("same.txt",b"SAME")])
                docs2=(await db.execute(select(Document).where(Document.original_filename=="same.txt"))).scalars().all()
                duplicate={"first_response_count":len(first) if isinstance(first,list) else None,
                    "second_response_count":len(second) if isinstance(second,list) else None,
                    "document_count":len(docs2),"distinct_stored_names":len({d.filename for d in docs2}),
                    "status_values":[d.approval_status for d in docs2]}
        output={"environment":"in-memory async SQLite + TemporaryDirectory; real upload handler; staff internal uploads remain pending; no network/background task", 
                "mixed_good_bad":mixed,"repeated_identical_upload":duplicate,
                "cleanup":"TemporaryDirectory removes files; DB engine disposed"}
    await eng.dispose()
    print(json.dumps(output,ensure_ascii=False))


asyncio.run(main())
