"""Explicit retention job. Dry-run by default; never scheduled on import/startup."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, delete
from app.models import ChatMessage, SystemChatLog, AuditEvent


async def apply_retention(db, *, now=None, execute=False):
    now = now or datetime.now(timezone.utc)
    naive = now.replace(tzinfo=None)
    policies = [
        ('chat_messages', ChatMessage, ChatMessage.created_at < naive-timedelta(days=90)),
        ('operational_logs', SystemChatLog, SystemChatLog.timestamp < now-timedelta(days=90)),
        ('audit_events', AuditEvent, AuditEvent.created_at < naive-timedelta(days=365)),
    ]
    result = {}
    for name, model, condition in policies:
        result[name] = (await db.execute(select(func.count()).select_from(model).where(condition))).scalar_one()
        if execute:
            await db.execute(delete(model).where(condition))
    if execute:
        await db.commit()
    return {'execute': execute, 'eligible': result}
