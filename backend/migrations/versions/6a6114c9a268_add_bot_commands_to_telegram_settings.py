"""add bot_commands_enabled and web_base_url to telegram settings

Revision ID: 6a6114c9a268
Revises: 2b06f03564ea
Create Date: 2026-09-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6a6114c9a268"
down_revision: str | None = "2b06f03564ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default=false backfills any existing row to the model's own default=False -
    # inbound bot commands are a different trust boundary than outbound pushes, so this
    # stays an explicit opt-in rather than defaulting on (docs/adr/0012-telegram-bot-polling.md).
    op.add_column(
        "telegram_settings",
        sa.Column(
            "bot_commands_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="Allow inbound Telegram bot commands (/lookup, /digest, /help). Off by "
            "default: a different trust boundary than outbound pushes, since the bot now acts "
            "on messages (see docs/adr/0012-telegram-bot-polling.md).",
        ),
    )
    op.add_column(
        "telegram_settings",
        sa.Column(
            "web_base_url",
            sa.String(length=500),
            nullable=False,
            server_default="",
            comment="Externally-reachable base URL of this Corvid instance, used only to "
            "build the /lookup command's web-UI deep link (Corvid has no public URL by default)",
        ),
    )


def downgrade() -> None:
    op.drop_column("telegram_settings", "web_base_url")
    op.drop_column("telegram_settings", "bot_commands_enabled")
