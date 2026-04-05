"""add_workspace_visibility_owner — add visibility + owner_id to knowledge_bases

Revision ID: 005_add_workspace_visibility
Revises: 004_add_document_fields
Create Date: 2026-04-04

Adds:
- knowledge_bases.visibility: "private" | "department" | "public"
  - "private": personal workspace, chỉ owner truy cập
  - "department": workspace phòng ban, member trong dept truy cập
  - "public": workspace công khai, tất cả user truy cập
- knowledge_bases.owner_id: FK -> users.id (chỉ dùng cho personal workspace)

Also updates default visibility of existing workspaces:
- department_id IS NOT NULL → visibility = "department"
- department_id IS NULL → visibility = "public"
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_add_workspace_visibility"
down_revision: Union[str, None] = "004_add_document_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add visibility column
    op.add_column(
        "knowledge_bases",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="department")
    )

    # 2. Add owner_id column
    op.add_column(
        "knowledge_bases",
        sa.Column("owner_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        "ix_knowledge_bases_owner_id",
        "knowledge_bases",
        ["owner_id"]
    )

    # 3. Update existing workspaces:
    #    - Có department_id → department workspace
    #    - Không có department_id → public workspace
    #    (owner_id stays NULL for existing records)
    op.execute("""
        UPDATE knowledge_bases
        SET visibility = CASE
            WHEN department_id IS NOT NULL THEN 'department'
            ELSE 'public'
        END
    """)

    # 4. Drop the unique constraint on department_id
    #    (now 1 department has 1 workspace via business logic, not DB constraint)
    op.execute("""
        ALTER TABLE knowledge_bases
        DROP CONSTRAINT IF EXISTS knowledge_bases_department_id_key
    """)


def downgrade() -> None:
    """Remove visibility + owner_id columns, restore unique constraint."""
    op.execute("""
        ALTER TABLE knowledge_bases
        ADD CONSTRAINT knowledge_bases_department_id_key UNIQUE (department_id)
    """)
    op.drop_index("ix_knowledge_bases_owner_id", table_name="knowledge_bases")
    op.drop_column("knowledge_bases", "owner_id")
    op.drop_column("knowledge_bases", "visibility")
