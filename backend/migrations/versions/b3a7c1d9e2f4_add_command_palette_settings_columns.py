"""add command palette settings columns

Revision ID: b3a7c1d9e2f4
Revises: dd4f2150142e
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3a7c1d9e2f4'
down_revision: Union[str, None] = 'dd4f2150142e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('general_settings')}

    with op.batch_alter_table('general_settings') as batch_op:
        if 'auto_open_on_single_match' not in existing_columns:
            batch_op.add_column(
                sa.Column('auto_open_on_single_match', sa.Boolean(), nullable=False, server_default=sa.true())
            )
        if 'start_screen' not in existing_columns:
            batch_op.add_column(
                sa.Column('start_screen', sa.String(length=20), nullable=False, server_default='search')
            )
        if 'always_tiles' not in existing_columns:
            batch_op.add_column(
                sa.Column('always_tiles', sa.Boolean(), nullable=False, server_default=sa.false())
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('general_settings')}

    with op.batch_alter_table('general_settings') as batch_op:
        if 'always_tiles' in existing_columns:
            batch_op.drop_column('always_tiles')
        if 'start_screen' in existing_columns:
            batch_op.drop_column('start_screen')
        if 'auto_open_on_single_match' in existing_columns:
            batch_op.drop_column('auto_open_on_single_match')
