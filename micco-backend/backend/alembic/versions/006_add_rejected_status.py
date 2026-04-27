"""add_rejected_status_to_documents — add REJECTED status to document status enum

Revision ID: 006_add_rejected_status
Revises: 005_add_workspace_visibility
Create Date: 2026-04-04

Adds:
- documents.status enum value: "REJECTED"
    When a document is rejected by an approver, status = "REJECTED"
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "006_add_rejected_status"
down_revision: Union[str, None] = "005_add_workspace_visibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add REJECTED to documents.status enum type."""
    # SQLAlchemy Enum(DocumentStatus) binds enum member names (uppercase),
    # so the PostgreSQL enum must include REJECTED.
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'documentstatus'
            ) AND NOT EXISTS (
                SELECT 1
                FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                WHERE t.typname = 'documentstatus'
                  AND e.enumlabel = 'REJECTED'
            ) THEN
                ALTER TYPE documentstatus ADD VALUE 'REJECTED';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove REJECTED from documents.status enum type."""
    # PostgreSQL doesn't support removing enum values, so we cannot downgrade
    # This is a known limitation of PostgreSQL enums
    pass

