"""add_rejected_status_to_documents — add REJECTED status to document status enum

Revision ID: 006_add_rejected_status
Revises: 005_add_workspace_visibility
Create Date: 2026-04-04

Adds:
- documents.status enum value: "rejected"
  When a document is rejected by an approver, status = "rejected"
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
    # PostgreSQL: Check if enum exists, if not create it; if yes, add value
    op.execute("""
        DO $$ BEGIN
            -- Try to add 'rejected' to existing enum
            ALTER TYPE documentstatus ADD VALUE 'rejected';
        EXCEPTION WHEN OTHERS THEN
            -- If enum doesn't exist or 'rejected' already exists, skip
            NULL;
        END $$;
    """)


def downgrade() -> None:
    """Remove REJECTED from documents.status enum type."""
    # PostgreSQL doesn't support removing enum values, so we cannot downgrade
    # This is a known limitation of PostgreSQL enums
    pass

