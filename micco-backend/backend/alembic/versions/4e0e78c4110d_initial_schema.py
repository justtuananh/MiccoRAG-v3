"""initial_schema — stamp existing tables, no-op (DB already exists)

Revision ID: 4e0e78c4110d
Revises:
Create Date: 2026-03-28 17:44:24.614363

This migration is a STAMP only — the database already contains all tables
created via docker/init-schema.sql and migrate_docs.py.
Alembic is now tracking the existing schema going forward.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4e0e78c4110d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: tables already exist. Alembic is now tracking this state."""
    pass


def downgrade() -> None:
    """No-op: do not drop production tables via alembic downgrade."""
    pass
