"""add single lookup history tables

Revision ID: f95a518b104a
Revises: d7bbfa4b19bb
Create Date: 2026-07-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f95a518b104a'
down_revision: Union[str, None] = 'd7bbfa4b19bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'single_lookup_searches' not in existing_tables:
        op.create_table(
            'single_lookup_searches',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('ioc', sa.String(length=2000), nullable=False),
            sa.Column('ioc_type', sa.String(length=20), nullable=False),
            sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_single_lookup_searches_ioc', 'single_lookup_searches', ['ioc'])
        op.create_index('ix_single_lookup_searches_ioc_type', 'single_lookup_searches', ['ioc_type'])

    if 'single_lookup_results' not in existing_tables:
        op.create_table(
            'single_lookup_results',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('search_id', sa.Integer(), sa.ForeignKey('single_lookup_searches.id', ondelete='CASCADE'), nullable=False),
            sa.Column('service_key', sa.String(length=100), nullable=False),
            sa.Column('service_name', sa.String(length=200), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('summary', sa.String(length=500), nullable=False),
            sa.Column('tlp', sa.String(length=20), nullable=False),
            sa.Column('data', sa.JSON(), nullable=True),
        )
        op.create_index('ix_single_lookup_results_search_id', 'single_lookup_results', ['search_id'])


def downgrade() -> None:
    op.drop_index('ix_single_lookup_results_search_id', table_name='single_lookup_results')
    op.drop_table('single_lookup_results')
    op.drop_index('ix_single_lookup_searches_ioc_type', table_name='single_lookup_searches')
    op.drop_index('ix_single_lookup_searches_ioc', table_name='single_lookup_searches')
    op.drop_table('single_lookup_searches')
