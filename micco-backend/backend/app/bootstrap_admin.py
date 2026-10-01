"""Explicit, one-time Admin creation for a freshly initialized database.

Run interactively with `python -m app.bootstrap_admin --name ... --email ...`.
Never invoked by application startup or Docker CMD.
"""
from __future__ import annotations

import argparse
import asyncio
import getpass

from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


async def create_admin(name: str, email: str, password: str) -> int:
    """Create exactly one active Admin, refusing any existing Admin or email."""
    settings.validate_runtime_security()
    async with AsyncSessionLocal() as db:
        # Prevent two interactive bootstrap commands from racing on an empty DB.
        await db.execute(text("SELECT pg_advisory_xact_lock(hashtext('miccorag_admin_bootstrap'))"))
        active_admin = (await db.execute(select(User.id).where(
            User.role == 'Admin', User.is_active.is_(True)).limit(1))).scalar_one_or_none()
        if active_admin is not None:
            raise RuntimeError('An active Admin already exists; bootstrap is disabled')
        existing_email = (await db.execute(select(User.id).where(
            func.lower(User.email) == email.lower()).limit(1))).scalar_one_or_none()
        if existing_email is not None:
            raise RuntimeError('That email already belongs to an account')
        user = User(name=name, email=email, hashed_password=hash_password(password),
                    role='Admin', department_id=None, is_active=True)
        db.add(user)
        await db.commit()
        return user.id


async def _bootstrap_and_close(name: str, email: str, password: str) -> int:
    try:
        return await create_admin(name, email, password)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description='One-time interactive Admin bootstrap')
    parser.add_argument('--name', required=True)
    parser.add_argument('--email', required=True)
    args = parser.parse_args()
    name = args.name.strip()
    email = args.email.strip().lower()
    if not 2 <= len(name) <= 100:
        parser.error('Name must be 2–100 characters')
    local, separator, domain = email.partition('@')
    if (len(email) > 255 or not separator or '@' in domain
            or not local or local.startswith('.') or local.endswith('.')
            or not domain or '.' not in domain or domain.startswith('.')
            or domain.endswith('.') or '..' in email or any(c.isspace() for c in email)):
        parser.error('Provide a valid email address')
    password = getpass.getpass('New Admin password: ')
    confirmation = getpass.getpass('Confirm password: ')
    if password != confirmation:
        parser.error('Passwords do not match')
    if len(password) < 12 or len(password.encode('utf-8')) > settings.COMPAT_BCRYPT_MAX_BYTES:
        parser.error('Password must be at least 12 characters and fit the bcrypt byte limit')
    try:
        user_id = asyncio.run(_bootstrap_and_close(name, email, password))
    except RuntimeError as exc:
        parser.exit(1, f'Admin bootstrap refused: {exc}\n')
    except Exception:
        parser.exit(1, 'Admin bootstrap failed; check database availability and schema\n')
    print(f'Created Admin id={user_id} email={email}')


if __name__ == '__main__':
    main()
