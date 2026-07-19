"""drop general_settings font column

Revision ID: dd4f2150142e
Revises: e8bc5a5afe8d
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'dd4f2150142e'
down_revision: Union[str, None] = 'e8bc5a5afe8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('general_settings')}

    if 'font' in existing_columns:
        with op.batch_alter_table('general_settings') as batch_op:
            batch_op.drop_column('font')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {col['name'] for col in inspector.get_columns('general_settings')}

    if 'font' not in existing_columns:
        with op.batch_alter_table('general_settings') as batch_op:
            batch_op.add_column(sa.Column('font', sa.String(length=50), nullable=False, server_default='Poppins'))
