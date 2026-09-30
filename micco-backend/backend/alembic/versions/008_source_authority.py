"""Explicit audited source authority; no inferred/backfilled authority ranks."""
from alembic import op
import sqlalchemy as sa
revision='008_source_authority'
down_revision='007_business_lifecycle'
branch_labels=None
depends_on=None

def upgrade():
    existing={c['name'] for c in sa.inspect(op.get_bind()).get_columns('documents')}
    for name,kind in [('issuer',sa.String(250)),('authority_scope',sa.String(250)),('authority_rank',sa.Integer()),('authority_verified_by',sa.Integer()),('authority_verified_at',sa.DateTime())]:
        if name not in existing:op.add_column('documents',sa.Column(name,kind,nullable=True))

def downgrade():
    for name in ['authority_verified_at','authority_verified_by','authority_rank','authority_scope','issuer']:
        op.drop_column('documents',name)
