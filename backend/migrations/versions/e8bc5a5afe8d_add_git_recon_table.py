"""add git recon table

Revision ID: e8bc5a5afe8d
Revises: d3f7a9c1e5b2
Create Date: 2026-07-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8bc5a5afe8d'
down_revision: Union[str, None] = 'd3f7a9c1e5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'git_recon_searches' not in existing_tables:
        op.create_table(
            'git_recon_searches',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('mode', sa.String(length=20), nullable=False),
            sa.Column('target', sa.String(length=300), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='completed'),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('repos_scanned', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('repos_failed', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('persons_found', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('result', sa.JSON(), nullable=True),
        )
        op.create_index('ix_git_recon_searches_target', 'git_recon_searches', ['target'])


def downgrade() -> None:
    op.drop_index('ix_git_recon_searches_target', table_name='git_recon_searches')
    op.drop_table('git_recon_searches')
