"""add_document_fields — category, tags, thumbnail for document metadata

Revision ID: 004_add_document_fields
Revises: 003_add_document_versions
Create Date: 2026-03-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_add_document_fields"
down_revision: Union[str, None] = "003_add_document_versions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add category, tags, and thumbnail columns to documents table."""
    op.add_column("documents", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("documents", sa.Column("tags", sa.Text(), nullable=True))  # stored as comma-separated
    op.add_column("documents", sa.Column("thumbnail", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove category, tags, thumbnail columns."""
    op.drop_column("documents", "thumbnail")
    op.drop_column("documents", "tags")
    op.drop_column("documents", "category")
