"""add reddit search tables

Revision ID: 6f5e11c0388f
Revises: addef49b4da3
Create Date: 2026-07-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6f5e11c0388f'
down_revision: Union[str, None] = 'addef49b4da3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'reddit_searches' not in existing_tables:
        op.create_table(
            'reddit_searches',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('subreddit_filter', sa.String(length=100), nullable=True),
            sa.Column('date_from', sa.Integer(), nullable=True),
            sa.Column('date_to', sa.Integer(), nullable=True),
            sa.Column('include_nsfw', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index('ix_reddit_searches_username', 'reddit_searches', ['username'])

    if 'reddit_search_results' not in existing_tables:
        op.create_table(
            'reddit_search_results',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('search_id', sa.Integer(), sa.ForeignKey('reddit_searches.id', ondelete='CASCADE'), nullable=False),
            sa.Column('kind', sa.String(length=10), nullable=False),
            sa.Column('reddit_id', sa.String(length=20), nullable=False),
            sa.Column('subreddit', sa.String(length=100), nullable=False),
            sa.Column('title', sa.Text(), nullable=True),
            sa.Column('body', sa.Text(), nullable=True),
            sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('num_comments', sa.Integer(), nullable=True),
            sa.Column('permalink', sa.String(length=500), nullable=False),
            sa.Column('created_utc', sa.Integer(), nullable=False),
            sa.Column('over_18', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('removed', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('extra', sa.JSON(), nullable=True),
            sa.UniqueConstraint('search_id', 'kind', 'reddit_id', name='uq_reddit_result_search_kind_id'),
        )
        op.create_index('ix_reddit_search_results_search_id', 'reddit_search_results', ['search_id'])
        op.create_index('ix_reddit_search_results_created_utc', 'reddit_search_results', ['created_utc'])


def downgrade() -> None:
    op.drop_index('ix_reddit_search_results_created_utc', table_name='reddit_search_results')
    op.drop_index('ix_reddit_search_results_search_id', table_name='reddit_search_results')
    op.drop_table('reddit_search_results')
    op.drop_index('ix_reddit_searches_username', table_name='reddit_searches')
    op.drop_table('reddit_searches')
