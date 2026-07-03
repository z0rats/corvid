"""add username search (maigret) tables

Revision ID: f9a8a3a5ef95
Revises: 30d1fe4ff7dc
Create Date: 2026-07-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f9a8a3a5ef95'
down_revision: Union[str, None] = '30d1fe4ff7dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'maigret_searches' not in existing_tables:
        op.create_table(
            'maigret_searches',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='running'),
            sa.Column('total_sites_checked', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('found_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('error_message', sa.String(length=1000), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index('ix_maigret_searches_username', 'maigret_searches', ['username'])
        op.create_index('ix_maigret_searches_status', 'maigret_searches', ['status'])

    if 'maigret_site_results' not in existing_tables:
        op.create_table(
            'maigret_site_results',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('search_id', sa.Integer(), sa.ForeignKey('maigret_searches.id', ondelete='CASCADE'), nullable=False),
            sa.Column('site_name', sa.String(length=200), nullable=False),
            sa.Column('url_user', sa.String(length=2000), nullable=False),
            sa.Column('http_status', sa.Integer(), nullable=True),
        )
        op.create_index('ix_maigret_site_results_search_id', 'maigret_site_results', ['search_id'])

    if 'username_search_config' not in existing_tables:
        op.create_table(
            'username_search_config',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
            sa.Column('max_concurrency', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('top_sites_count', sa.Integer(), nullable=False, server_default='500'),
            sa.Column('proxy_url', sa.String(length=500), nullable=True),
        )


def downgrade() -> None:
    op.drop_table('username_search_config')
    op.drop_index('ix_maigret_site_results_search_id', table_name='maigret_site_results')
    op.drop_table('maigret_site_results')
    op.drop_index('ix_maigret_searches_status', table_name='maigret_searches')
    op.drop_index('ix_maigret_searches_username', table_name='maigret_searches')
    op.drop_table('maigret_searches')
