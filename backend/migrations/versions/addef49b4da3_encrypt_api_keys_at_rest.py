"""encrypt api keys at rest

Revision ID: addef49b4da3
Revises: 60fbe30455a1
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.security.secrets_crypto import encrypt_value, decrypt_value


revision: str = 'addef49b4da3'
down_revision: Union[str, None] = '60fbe30455a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # batch mode is required for SQLite, which has no native ALTER COLUMN TYPE
    with op.batch_alter_table('apikeys') as batch_op:
        batch_op.alter_column(
            'key',
            existing_type=sa.String(length=500),
            type_=sa.Text(),
        )

    conn = op.get_bind()
    apikeys = sa.table('apikeys', sa.column('name', sa.String), sa.column('key', sa.Text))
    rows = conn.execute(sa.select(apikeys.c.name, apikeys.c.key)).fetchall()
    for name, key in rows:
        if not key:
            continue
        # decrypt_value() returns its input unchanged when it isn't a valid Fernet
        # token - i.e. this row still holds plaintext from before encryption existed.
        if decrypt_value(key) == key:
            conn.execute(
                apikeys.update().where(apikeys.c.name == name).values(key=encrypt_value(key))
            )


def downgrade() -> None:
    conn = op.get_bind()
    apikeys = sa.table('apikeys', sa.column('name', sa.String), sa.column('key', sa.Text))
    rows = conn.execute(sa.select(apikeys.c.name, apikeys.c.key)).fetchall()
    for name, key in rows:
        if not key:
            continue
        conn.execute(
            apikeys.update().where(apikeys.c.name == name).values(key=decrypt_value(key))
        )

    with op.batch_alter_table('apikeys') as batch_op:
        batch_op.alter_column(
            'key',
            existing_type=sa.Text(),
            type_=sa.String(length=500),
        )
