"""default newsfeed article retention to 30 days

Revision ID: e4b7a2c91d06
Revises: c5e18a3d9f20
Create Date: 2026-10-14 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4b7a2c91d06"
down_revision: str | None = "c5e18a3d9f20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Data-only: `retention_days` was 0 ("unlimited") by default, but nothing ever deleted old
    # articles, so the table grew without bound. 30 days is the new default; an explicit 0 can't
    # be told apart from the old default, so every unlimited row moves to 30 (re-selectable in
    # Settings). Annotated/analyzed articles are kept regardless (`delete_old_news_articles`).
    op.execute("UPDATE newsfeed_config SET retention_days = 30 WHERE retention_days = 0")


def downgrade() -> None:
    # Not reversible: which rows were 0 before the upgrade isn't recorded, and articles already
    # pruned under the new default can't be restored (data/backups/ holds the pre-migration copy).
    pass
