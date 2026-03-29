"""add_rls_policies — enable PostgreSQL row-level security on documents and knowledge_entries

Revision ID: 002_add_rls_policies
Revises: 4e0e78c4110d
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_rls_policies'
down_revision: Union[str, None] = '4e0e78c4110d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create department-based access policies."""
    # --- documents table ---
    op.execute("ALTER TABLE documents ENABLE ROW LEVEL SECURITY")

    # Admin bypass
    op.execute("""
        CREATE POLICY doc_admin_policy ON documents
        FOR ALL USING (current_setting('app.user_role', true) = 'Admin')
    """)

    # Department + visibility + uploader access
    op.execute("""
        CREATE POLICY doc_dept_policy ON documents
        FOR ALL USING (
            visibility = 'public'
            OR department_id = (current_setting('app.user_dept_id', true)::int)
            OR uploader_id = (current_setting('app.user_id', true)::int)
        )
    """)

    # --- knowledge_entries table ---
    op.execute("ALTER TABLE knowledge_entries ENABLE ROW LEVEL SECURITY")

    # Admin bypass
    op.execute("""
        CREATE POLICY kn_admin_policy ON knowledge_entries
        FOR ALL USING (current_setting('app.user_role', true) = 'Admin')
    """)

    # Department + visibility + owner access
    op.execute("""
        CREATE POLICY kn_dept_policy ON knowledge_entries
        FOR ALL USING (
            visibility = 'public'
            OR department_id = (current_setting('app.user_dept_id', true)::int)
            OR owner_id = (current_setting('app.user_id', true)::int)
        )
    """)


def downgrade() -> None:
    """Drop RLS policies and disable RLS."""
    # documents
    op.execute("DROP POLICY IF EXISTS doc_admin_policy ON documents")
    op.execute("DROP POLICY IF EXISTS doc_dept_policy ON documents")
    op.execute("ALTER TABLE documents DISABLE ROW LEVEL SECURITY")

    # knowledge_entries
    op.execute("DROP POLICY IF EXISTS kn_admin_policy ON knowledge_entries")
    op.execute("DROP POLICY IF EXISTS kn_dept_policy ON knowledge_entries")
    op.execute("ALTER TABLE knowledge_entries DISABLE ROW LEVEL SECURITY")
