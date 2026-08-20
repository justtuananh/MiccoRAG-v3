import asyncio
import sys
from sqlalchemy.future import select
from app.core._db_session import AsyncSessionLocal
from app.models.user import User
from app.api.compat import get_allowed_document_ids

async def main():
    async with AsyncSessionLocal() as session:
        # Get users
        users = await session.execute(select(User))
        for u in users.scalars().all():
            try:
                allowed_ids = await get_allowed_document_ids(session, u, 1)
                print(f"User {u.username} (Role: {u.role}) allowed IDs for WS 1: {allowed_ids}")
            except Exception as e:
                print(f"Error checking user {u.username}: {e}")

if __name__ == "__main__":
    sys.path.append("/home/kms/MiccoRAG-v3/micco-backend/backend")
    import app.api_compat.documents  # Might need to see where get_allowed_document_ids is
    # Just a mock import to find it
