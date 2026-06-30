"""add language column to general_settings

Revision ID: 30d1fe4ff7dc
Revises: 62cc3a19e64c
Create Date: 2026-06-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '30d1fe4ff7dc'
down_revision: Union[str, None] = '62cc3a19e64c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info('general_settings')"))
    columns = [row[1] for row in result]

    if not columns:
        # Table doesn't exist yet; it will be created with the new column by
        # Base.metadata.create_all() on first app startup.
        return

    if 'language' not in columns:
        op.add_column(
            'general_settings',
            sa.Column('language', sa.String(length=5), nullable=False, server_default='en')
        )


def downgrade() -> None:
    op.drop_column('general_settings', 'language')
