"""add email search pypi version-check columns

Revision ID: 60fbe30455a1
Revises: 70976b3ed331
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '60fbe30455a1'
down_revision: Union[str, None] = '70976b3ed331'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c['name'] for c in inspector.get_columns('email_search_config')}

    if 'latest_pypi_version' not in existing_columns:
        op.add_column('email_search_config', sa.Column('latest_pypi_version', sa.String(length=50), nullable=True))

    if 'pypi_checked_at' not in existing_columns:
        op.add_column('email_search_config', sa.Column('pypi_checked_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('email_search_config', 'pypi_checked_at')
    op.drop_column('email_search_config', 'latest_pypi_version')
