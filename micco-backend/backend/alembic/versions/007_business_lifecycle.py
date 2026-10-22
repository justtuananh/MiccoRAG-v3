"""Business lifecycle metadata; historical effective dates remain unknown.

Revision ID: 007_business_lifecycle
Revises: 006_add_rejected_status
"""
from alembic import op
import sqlalchemy as sa

revision = "007_business_lifecycle"
down_revision = "006_add_rejected_status"
branch_labels = None
depends_on = None


def _add(table, column):
    bind = op.get_bind()
    if column.name not in {c["name"] for c in sa.inspect(bind).get_columns(table)}:
        op.add_column(table, column)


def upgrade():
    from app.models.upload_receipt import UploadReceipt
    UploadReceipt.__table__.create(op.get_bind(), checkfirst=True)
    from app.models.audit_event import AuditEvent
    AuditEvent.__table__.create(op.get_bind(), checkfirst=True)
    for table in ("documents", "knowledge_entries"):
        _add(table, sa.Column("effective_from", sa.Date(), nullable=True))
        _add(table, sa.Column("effective_until", sa.Date(), nullable=True))
        _add(table, sa.Column("approved_by", sa.Integer(), nullable=True))
        _add(table, sa.Column("approved_at", sa.DateTime(), nullable=True))
        _add(table, sa.Column("deleted_at", sa.DateTime(), nullable=True))
    _add("documents", sa.Column("index_cleaned_at", sa.DateTime(), nullable=True))
    _add("documents", sa.Column("index_cleanup_attempts", sa.Integer(), nullable=False, server_default="0"))
    _add("documents", sa.Column("index_cleanup_error", sa.String(200), nullable=True))
    _add("documents", sa.Column("knowledge_entry_id", sa.Integer(), nullable=True))
    _add("knowledge_entries", sa.Column("supersedes_entry_id", sa.Integer(), nullable=True))
    _add("documents", sa.Column("content_hash", sa.String(64), nullable=True))
    _add("documents", sa.Column("supersedes_document_id", sa.Integer(), nullable=True))
    _add("knowledge_bases", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    _add("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    _add("departments", sa.Column("code", sa.String(100), nullable=True))
    _add("departments", sa.Column("kind", sa.String(30), nullable=False, server_default="standard"))
    op.execute(sa.text("UPDATE departments SET kind = 'directorate' WHERE id IN (SELECT department_id FROM users WHERE role IN ('Giám đốc', 'Phó giám đốc') AND department_id IS NOT NULL)"))
    for name, column in (
        ("approval_status", sa.Column("approval_status", sa.String(20), nullable=False, server_default="pending")),
        ("processing_status", sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending")),
        ("effective_from", sa.Column("effective_from", sa.Date(), nullable=True)),
        ("effective_until", sa.Column("effective_until", sa.Date(), nullable=True)),
        ("approved_by", sa.Column("approved_by", sa.Integer(), nullable=True)),
        ("approved_at", sa.Column("approved_at", sa.DateTime(), nullable=True)),
        ("supersedes_version_id", sa.Column("supersedes_version_id", sa.Integer(), nullable=True)),
        ("document_ref_id", sa.Column("document_ref_id", sa.Integer(), nullable=True)),
    ):
        _add("document_versions", column)
    # Existing rows keep NULL effective dates. No approval or publication date is inferred.


def downgrade():
    for table, names in (
        ("document_versions", ("document_ref_id", "supersedes_version_id", "approved_at", "approved_by", "effective_until", "effective_from", "processing_status", "approval_status")),
        ("departments", ("kind", "code")),
        ("users", ("is_active",)),
        ("knowledge_bases", ("deleted_at",)),
        ("documents", ("knowledge_entry_id", "supersedes_document_id", "content_hash", "deleted_at", "approved_at", "approved_by", "effective_until", "effective_from")),
        ("knowledge_entries", ("supersedes_entry_id", "deleted_at", "approved_at", "approved_by", "effective_until", "effective_from")),
    ):
        existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}
        for name in names:
            if name in existing:
                op.drop_column(table, name)
