import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_chat_log import SystemChatLog

logger = logging.getLogger(__name__)

async def log_system_chat(
    db: AsyncSession,
    workspace_id: int,
    question: str,
    answer: str,
    method: str,
    response_time: float,
    ip_address: str | None = None,
) -> None:
    """
    Log a chat interaction to the system_chat_logs table for optimization.
    This is called asynchronously after a response is generated.
    """
    try:
        # Vietnam timezone (UTC+7)
        vn_now = datetime.now(timezone(timedelta(hours=7)))
        
        log_entry = SystemChatLog(
            workspace_id=workspace_id,
            ip_address=ip_address,
            question=question,
            answer=answer,
            method=method,
            response_time=response_time,
            timestamp=vn_now
        )
        db.add(log_entry)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log system chat: {e}")
        await db.rollback()
