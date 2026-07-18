"""add newsfeed fetch health columns

Revision ID: d3f7a9c1e5b2
Revises: a1c2e4f6b8d0
Create Date: 2026-07-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3f7a9c1e5b2'
down_revision: Union[str, None] = 'a1c2e4f6b8d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c['name'] for c in inspector.get_columns('newsfeed_settings')}

    if 'last_fetched_at' not in existing_columns:
        op.add_column('newsfeed_settings', sa.Column('last_fetched_at', sa.DateTime(timezone=True), nullable=True))

    if 'last_success_at' not in existing_columns:
        op.add_column('newsfeed_settings', sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True))

    if 'last_error' not in existing_columns:
        op.add_column('newsfeed_settings', sa.Column('last_error', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('newsfeed_settings', 'last_error')
    op.drop_column('newsfeed_settings', 'last_success_at')
    op.drop_column('newsfeed_settings', 'last_fetched_at')
