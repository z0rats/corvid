"""add notify_newsfeed_matches to telegram settings

Revision ID: 2b06f03564ea
Revises: 5ffc21f237b6
Create Date: 2026-09-08 15:17:08.975664

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b06f03564ea"
down_revision: str | None = "5ffc21f237b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default backfills any existing row (a fresh install has none yet,
    # but an upgraded deployment may already have a configured telegram_settings
    # row) - matches the model's own default=True.
    op.add_column(
        "telegram_settings",
        sa.Column(
            "notify_newsfeed_matches",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
            comment="Notify when a newsfeed article matches a watchlist keyword",
        ),
    )


def downgrade() -> None:
    op.drop_column("telegram_settings", "notify_newsfeed_matches")
