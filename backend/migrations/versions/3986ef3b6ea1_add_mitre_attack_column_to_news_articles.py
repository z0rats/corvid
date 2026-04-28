"""add mitre_attack column to news_articles

Revision ID: 3986ef3b6ea1
Revises:
Create Date: 2026-04-27 22:08:35.847722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3986ef3b6ea1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info('news_articles')"))
    columns = [row[1] for row in result]

    if 'threat_intel' in columns:
        op.alter_column('news_articles', 'threat_intel', new_column_name='mitre_attack')
    elif 'mitre_attack' not in columns:
        op.add_column('news_articles', sa.Column('mitre_attack', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('news_articles', 'mitre_attack')
