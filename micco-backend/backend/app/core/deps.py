from sqlalchemy.ext.asyncio import AsyncSession
from anyio import CancelScope
from app.core.database import AsyncSessionLocal


async def get_db() -> AsyncSession:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        # Client disconnects cancel the request scope; returning its pooled
        # connection must still finish before that cancellation propagates.
        with CancelScope(shield=True):
            await session.close()
