"""add email search (mailcat) tables

Revision ID: 70976b3ed331
Revises: 1b14c9d434cb
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '70976b3ed331'
down_revision: Union[str, None] = '1b14c9d434cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'mail_searches' not in existing_tables:
        op.create_table(
            'mail_searches',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='running'),
            sa.Column('total_providers_checked', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('found_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('error_message', sa.String(length=1000), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index('ix_mail_searches_username', 'mail_searches', ['username'])
        op.create_index('ix_mail_searches_status', 'mail_searches', ['status'])

    if 'mail_search_results' not in existing_tables:
        op.create_table(
            'mail_search_results',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('search_id', sa.Integer(), sa.ForeignKey('mail_searches.id', ondelete='CASCADE'), nullable=False),
            sa.Column('provider_name', sa.String(length=200), nullable=False),
            sa.Column('emails', sa.JSON(), nullable=False),
            sa.Column('extra', sa.JSON(), nullable=True),
        )
        op.create_index('ix_mail_search_results_search_id', 'mail_search_results', ['search_id'])

    if 'email_search_config' not in existing_tables:
        op.create_table(
            'email_search_config',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('max_concurrency', sa.Integer(), nullable=False, server_default='10'),
            sa.Column('proxy_url', sa.String(length=500), nullable=True),
            sa.Column('use_tor', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('enable_smtp_checks', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('enable_headless_checks', sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    op.drop_table('email_search_config')
    op.drop_index('ix_mail_search_results_search_id', table_name='mail_search_results')
    op.drop_table('mail_search_results')
    op.drop_index('ix_mail_searches_status', table_name='mail_searches')
    op.drop_index('ix_mail_searches_username', table_name='mail_searches')
    op.drop_table('mail_searches')
