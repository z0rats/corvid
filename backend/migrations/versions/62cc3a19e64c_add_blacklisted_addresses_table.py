"""add blacklisted_addresses table

Revision ID: 62cc3a19e64c
Revises: 3986ef3b6ea1
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '62cc3a19e64c'
down_revision: Union[str, None] = '3986ef3b6ea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'blacklisted_addresses' in inspector.get_table_names():
        return

    op.create_table(
        'blacklisted_addresses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('address', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('chain', sa.String(length=20), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('entity_name', sa.String(length=255), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('address', 'source', name='uq_blacklist_address_source'),
    )
    op.create_index('ix_blacklisted_addresses_address', 'blacklisted_addresses', ['address'])
    op.create_index('ix_blacklisted_addresses_source', 'blacklisted_addresses', ['source'])


def downgrade() -> None:
    op.drop_index('ix_blacklisted_addresses_source', table_name='blacklisted_addresses')
    op.drop_index('ix_blacklisted_addresses_address', table_name='blacklisted_addresses')
    op.drop_table('blacklisted_addresses')
