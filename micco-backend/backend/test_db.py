import asyncio
from sqlalchemy import select
from app.core.deps import get_db
from app.models.document import Document

async def main():
    async for db in get_db():
        result = await db.execute(select(Document.file_type).distinct())
        print(result.all())

asyncio.run(main())
