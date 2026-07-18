"""add maigret pypi version-check columns

Revision ID: a1c2e4f6b8d0
Revises: 6f5e11c0388f
Create Date: 2026-07-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c2e4f6b8d0'
down_revision: Union[str, None] = '6f5e11c0388f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c['name'] for c in inspector.get_columns('username_search_config')}

    if 'latest_pypi_version' not in existing_columns:
        op.add_column('username_search_config', sa.Column('latest_pypi_version', sa.String(length=50), nullable=True))

    if 'pypi_checked_at' not in existing_columns:
        op.add_column('username_search_config', sa.Column('pypi_checked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('username_search_config', 'pypi_checked_at')
    op.drop_column('username_search_config', 'latest_pypi_version')
