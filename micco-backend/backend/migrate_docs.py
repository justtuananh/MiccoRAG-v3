import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.core.config import settings

async def main():
    engine = create_async_engine(str(settings.DATABASE_URL))
    print(f"Connecting to {settings.DATABASE_URL}...")
    
    async with engine.begin() as conn:
        print("Checking if columns exist...")
        
        # We wrap in try-except because some columns might already exist
        queries = [
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploader_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL;",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'internal';",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) DEFAULT 'approved';",
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS approval_note TEXT;"
        ]
        
        for q in queries:
            print(f"Executing: {q}")
            await conn.execute(text(q))
            
        print("Migration done.")
        
if __name__ == "__main__":
    asyncio.run(main())
