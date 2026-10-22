"""Store KB-local extracted-text duplicate decisions."""
from alembic import op
import sqlalchemy as sa

revision = '010_text_duplicate'
down_revision = '009_lifecycle_foreign_keys'
branch_labels = None
depends_on = None


def upgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('documents')}
    with op.batch_alter_table('documents') as batch:
        if 'text_fingerprint' not in columns:
            batch.add_column(sa.Column('text_fingerprint', sa.String(64), nullable=True))
        if 'duplicate_of_document_id' not in columns:
            batch.add_column(sa.Column('duplicate_of_document_id', sa.Integer(), nullable=True))
        if 'near_duplicate_document_id' not in columns:
            batch.add_column(sa.Column('near_duplicate_document_id', sa.Integer(), nullable=True))
        if 'duplicate_similarity' not in columns:
            batch.add_column(sa.Column('duplicate_similarity', sa.Float(), nullable=True))
    inspector = sa.inspect(op.get_bind())
    indexes = {index['name'] for index in inspector.get_indexes('documents')}
    if 'ix_documents_workspace_text_fingerprint' not in indexes:
        op.create_index('ix_documents_workspace_text_fingerprint', 'documents',
                        ['workspace_id', 'text_fingerprint'])
    foreign_keys = {tuple(fk['constrained_columns']) for fk in inspector.get_foreign_keys('documents')}
    with op.batch_alter_table('documents') as batch:
        if ('duplicate_of_document_id',) not in foreign_keys:
            batch.create_foreign_key('fk_documents_duplicate_of_document_id', 'documents',
                                     ['duplicate_of_document_id'], ['id'], ondelete='SET NULL')
        if ('near_duplicate_document_id',) not in foreign_keys:
            batch.create_foreign_key('fk_documents_near_duplicate_document_id', 'documents',
                                     ['near_duplicate_document_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('documents') as batch:
        batch.drop_constraint('fk_documents_near_duplicate_document_id', type_='foreignkey')
        batch.drop_constraint('fk_documents_duplicate_of_document_id', type_='foreignkey')
    op.drop_index('ix_documents_workspace_text_fingerprint', table_name='documents')
    with op.batch_alter_table('documents') as batch:
        batch.drop_column('duplicate_similarity')
        batch.drop_column('near_duplicate_document_id')
        batch.drop_column('duplicate_of_document_id')
        batch.drop_column('text_fingerprint')
