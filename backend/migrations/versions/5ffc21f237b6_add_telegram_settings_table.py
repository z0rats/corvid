"""add telegram settings table

Revision ID: 5ffc21f237b6
Revises: 0d039633c0b7
Create Date: 2026-09-08 13:39:58.863519

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.core.security.secrets_crypto

# revision identifiers, used by Alembic.
revision: str = "5ffc21f237b6"
down_revision: str | None = "0d039633c0b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_settings",
        sa.Column("id", sa.Integer(), nullable=False, comment="Singleton row id, always 1"),
        sa.Column(
            "bot_token",
            app.core.security.secrets_crypto.EncryptedString(),
            nullable=False,
            comment="Telegram bot token from @BotFather (encrypted at rest)",
        ),
        sa.Column(
            "chat_id",
            sa.String(length=100),
            nullable=False,
            comment="Telegram chat ID notifications are sent to",
        ),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, comment="Master switch for Telegram delivery"
        ),
        sa.Column(
            "notify_scan_events",
            sa.Boolean(),
            nullable=False,
            comment="Notify on scan completed/cancelled (failures always notify while enabled)",
        ),
        sa.Column(
            "notify_job_failures",
            sa.Boolean(),
            nullable=False,
            comment="Notify when a recurring scheduler job starts or stops failing",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
            comment="When this row was created",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
            comment="When this row was last updated",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("telegram_settings")
