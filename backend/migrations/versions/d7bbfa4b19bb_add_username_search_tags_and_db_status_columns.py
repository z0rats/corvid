"""add username search tags and db-status columns

Revision ID: d7bbfa4b19bb
Revises: f9a8a3a5ef95
Create Date: 2026-07-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7bbfa4b19bb'
down_revision: Union[str, None] = 'f9a8a3a5ef95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    search_columns = {c['name'] for c in inspector.get_columns('maigret_searches')}
    if 'tags' not in search_columns:
        op.add_column('maigret_searches', sa.Column('tags', sa.JSON(), nullable=True))

    config_columns = {c['name'] for c in inspector.get_columns('username_search_config')}
    if 'auto_update_db_enabled' not in config_columns:
        op.add_column(
            'username_search_config',
            sa.Column('auto_update_db_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if 'auto_update_interval_hours' not in config_columns:
        op.add_column(
            'username_search_config',
            sa.Column('auto_update_interval_hours', sa.Integer(), nullable=False, server_default='24'),
        )
    if 'db_last_updated_at' not in config_columns:
        op.add_column('username_search_config', sa.Column('db_last_updated_at', sa.DateTime(timezone=True), nullable=True))
    if 'db_site_count' not in config_columns:
        op.add_column(
            'username_search_config',
            sa.Column('db_site_count', sa.Integer(), nullable=False, server_default='0'),
        )


def downgrade() -> None:
    op.drop_column('username_search_config', 'db_site_count')
    op.drop_column('username_search_config', 'db_last_updated_at')
    op.drop_column('username_search_config', 'auto_update_interval_hours')
    op.drop_column('username_search_config', 'auto_update_db_enabled')
    op.drop_column('maigret_searches', 'tags')
