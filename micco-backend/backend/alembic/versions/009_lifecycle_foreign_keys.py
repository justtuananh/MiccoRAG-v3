"""Align lifecycle foreign keys with ORM metadata on upgraded databases."""
from alembic import op
import sqlalchemy as sa
revision = '009_lifecycle_foreign_keys'
down_revision = '008_source_authority'
branch_labels = None
depends_on = None

REFERENCES = {
    'documents': {'approved_by': 'users', 'knowledge_entry_id': 'knowledge_entries',
                  'supersedes_document_id': 'documents', 'authority_verified_by': 'users'},
    'knowledge_entries': {'approved_by': 'users', 'supersedes_entry_id': 'knowledge_entries'},
    'document_versions': {'approved_by': 'users', 'supersedes_version_id': 'document_versions',
                          'document_ref_id': 'documents'},
}


def upgrade():
    for table, references in REFERENCES.items():
        existing = {tuple(fk['constrained_columns']) for fk in sa.inspect(op.get_bind()).get_foreign_keys(table)}
        missing = [(column, target) for column, target in references.items() if (column,) not in existing]
        if missing:
            with op.batch_alter_table(table) as batch:
                for column, target in missing:
                    batch.create_foreign_key(f'fk_{table}_{column}_lifecycle', target, [column], ['id'], ondelete='SET NULL')


def downgrade():
    for table, references in reversed(list(REFERENCES.items())):
        names = {fk['name'] for fk in sa.inspect(op.get_bind()).get_foreign_keys(table)}
        removable = [f'fk_{table}_{column}_lifecycle' for column in references if f'fk_{table}_{column}_lifecycle' in names]
        if removable:
            with op.batch_alter_table(table) as batch:
                for name in removable:
                    batch.drop_constraint(name, type_='foreignkey')
