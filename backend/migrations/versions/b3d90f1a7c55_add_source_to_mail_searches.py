"""add source and error_count to mail_searches

Revision ID: b3d90f1a7c55
Revises: a7c41e90b3d2
Create Date: 2026-10-05 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3d90f1a7c55"
down_revision: str | None = "a7c41e90b3d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Plain ADD COLUMN, not batch_alter_table: on SQLite a batch recreates `mail_searches`, and with
    # the app's `PRAGMA foreign_keys=ON` that cascades into every `mail_search_results` row.
    op.add_column(
        "mail_searches",
        sa.Column(
            "source",
            sa.String(length=30),
            nullable=False,
            server_default="mailcat",
            comment=(
                "Which tool produced this run: 'mailcat' (username probed at mail providers) "
                "or 'user_scanner' (full address checked at ~150 services)"
            ),
        ),
    )
    op.add_column(
        "mail_searches",
        sa.Column(
            "error_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment=(
                "user_scanner only: checks that failed (blocked, timed out, changed) rather than "
                "answered, so they aren't read as 'not registered'"
            ),
        ),
    )
    op.create_index(op.f("ix_mail_searches_source"), "mail_searches", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mail_searches_source"), table_name="mail_searches")
    op.drop_column("mail_searches", "error_count")
    op.drop_column("mail_searches", "source")
