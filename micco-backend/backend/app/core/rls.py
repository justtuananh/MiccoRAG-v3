"""
Row-Level Security (RLS) utilities for PostgreSQL.

Sets session variables that RLS policies reference so that PostgreSQL
enforces department-based row isolation at the database level.

Usage:
    In FastAPI dependencies or background tasks where you have a User object,
    call `await set_rls_context(db, user)` before running queries.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.user import User


async def set_rls_context(db: AsyncSession, user: User) -> None:
    """Set PostgreSQL session variables for RLS policy evaluation.

    Must be called within the same transaction before any SELECT on
    tables with RLS enabled.
    """
    await db.execute(
        text("SET LOCAL app.user_id = :uid"),
        {"uid": user.id}
    )
    await db.execute(
        text("SET LOCAL app.user_role = :role"),
        {"role": user.role}
    )
    await db.execute(
        text("SET LOCAL app.user_dept_id = :dept"),
        {"dept": user.department_id or 0}
    )


async def clear_rls_context(db: AsyncSession) -> None:
    """Clear RLS session variables (called on transaction end)."""
    await db.execute(text("RESET app.user_id"))
    await db.execute(text("RESET app.user_role"))
    await db.execute(text("RESET app.user_dept_id"))
