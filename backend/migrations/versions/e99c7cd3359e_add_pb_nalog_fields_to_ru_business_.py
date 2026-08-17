"""add pb_nalog fields to ru_business_check

Revision ID: e99c7cd3359e
Revises: b79d3edf3292
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e99c7cd3359e"
down_revision: str | None = "b79d3edf3292"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "pb_nalog_data",
            sa.JSON(),
            nullable=True,
            comment="Прозрачный бизнес result: {checked, found, mass_address_count, "
            "mass_address_companies, director_indicator, profile_url}",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "pb_nalog_raw",
            sa.Text(),
            nullable=True,
            comment="Verbatim search+detail payload as received from pb.nalog.ru",
        ),
    )
    # server_default backfills existing rows - SQLite's ALTER TABLE ADD COLUMN ... NOT NULL
    # requires a server-side value, same reasoning as the arbitration-thresholds migration.
    op.add_column(
        "ru_business_check_settings",
        sa.Column(
            "mass_address_threshold",
            sa.Integer(),
            nullable=False,
            server_default="10",
            comment="Number of other entities registered at the same address (pb.nalog.ru) "
            "at/above which the 'mass registration address' soft flag fires",
        ),
    )


def downgrade() -> None:
    op.drop_column("ru_business_check_settings", "mass_address_threshold")
    op.drop_column("ru_business_check_searches", "pb_nalog_raw")
    op.drop_column("ru_business_check_searches", "pb_nalog_data")
