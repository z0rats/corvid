"""add social-analyzer as a username search source

Revision ID: 1b14c9d434cb
Revises: f95a518b104a
Create Date: 2026-07-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1b14c9d434cb'
down_revision: Union[str, None] = 'f95a518b104a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    search_columns = {c['name'] for c in inspector.get_columns('maigret_searches')}
    if 'source' not in search_columns:
        op.add_column(
            'maigret_searches',
            sa.Column('source', sa.String(length=30), nullable=False, server_default='maigret'),
        )
        op.create_index('ix_maigret_searches_source', 'maigret_searches', ['source'])

    result_columns = {c['name'] for c in inspector.get_columns('maigret_site_results')}
    if 'extra' not in result_columns:
        op.add_column('maigret_site_results', sa.Column('extra', sa.JSON(), nullable=True))

    if 'social_analyzer_config' not in inspector.get_table_names():
        op.create_table(
            'social_analyzer_config',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('top_sites_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('latest_pypi_version', sa.String(length=50), nullable=True),
            sa.Column('pypi_checked_at', sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    op.drop_table('social_analyzer_config')
    op.drop_column('maigret_site_results', 'extra')
    op.drop_index('ix_maigret_searches_source', table_name='maigret_searches')
    op.drop_column('maigret_searches', 'source')
