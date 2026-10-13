"""add reliability to newsfeed_settings

Revision ID: a7c41e90b3d2
Revises: 43f3a99819ae
Create Date: 2026-10-05 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c41e90b3d2"
down_revision: str | None = "43f3a99819ae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECK_NAME = "ck_newsfeed_settings_reliability"
CHECK_EXPR = "reliability IS NULL OR reliability IN ('A', 'B', 'C', 'D', 'E', 'F')"


def upgrade() -> None:
    # Deliberately not `batch_alter_table`: on SQLite that recreates the table, and the app
    # runs with `PRAGMA foreign_keys=ON`, so dropping the old `newsfeed_settings` cascades
    # `ON DELETE CASCADE` into every `news_articles` row. Plain ALTER TABLE keeps them.
    if op.get_bind().dialect.name == "sqlite":
        op.execute(
            f"ALTER TABLE newsfeed_settings ADD COLUMN reliability VARCHAR(1) "
            f"CONSTRAINT {CHECK_NAME} CHECK ({CHECK_EXPR})"
        )
        return

    op.add_column("newsfeed_settings", sa.Column("reliability", sa.String(length=1), nullable=True))
    op.create_check_constraint(CHECK_NAME, "newsfeed_settings", CHECK_EXPR)


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint(CHECK_NAME, "newsfeed_settings", type_="check")
    # SQLite drops the column together with its own column-level CHECK.
    op.drop_column("newsfeed_settings", "reliability")
