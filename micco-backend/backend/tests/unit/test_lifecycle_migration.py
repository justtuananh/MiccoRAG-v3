"""Legacy schema receives actual foreign-key constraints, not only ORM metadata."""
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_lifecycle_foreign_keys_idempotent_and_enforced():
    path = Path(__file__).resolve().parents[2] / 'alembic/versions/009_lifecycle_foreign_keys.py'
    spec = importlib.util.spec_from_file_location('lifecycle_keys', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine('sqlite://')
    metadata = sa.MetaData()
    sa.Table('users', metadata, sa.Column('id', sa.Integer, primary_key=True))
    for table, references in migration.REFERENCES.items():
        sa.Table(table, metadata, sa.Column('id', sa.Integer, primary_key=True),
                 *(sa.Column(column, sa.Integer, nullable=True) for column in references))
    with engine.begin() as conn:
        conn.exec_driver_sql('PRAGMA foreign_keys=ON')
        metadata.create_all(conn)
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
            migration.upgrade()
        for table, references in migration.REFERENCES.items():
            keys = sa.inspect(conn).get_foreign_keys(table)
            assert {fk['constrained_columns'][0] for fk in keys} == set(references)
        conn.exec_driver_sql('INSERT INTO users (id) VALUES (1)')
        conn.exec_driver_sql('INSERT INTO documents (id, authority_verified_by) VALUES (1, 1)')
        conn.exec_driver_sql('DELETE FROM users WHERE id=1')
        assert conn.exec_driver_sql('SELECT authority_verified_by FROM documents WHERE id=1').scalar() is None
        with pytest.raises(sa.exc.IntegrityError):
            conn.exec_driver_sql('INSERT INTO documents (id, authority_verified_by) VALUES (2, 999)')
        with Operations.context(MigrationContext.configure(conn)):
            migration.downgrade()
        assert not sa.inspect(conn).get_foreign_keys('documents')
