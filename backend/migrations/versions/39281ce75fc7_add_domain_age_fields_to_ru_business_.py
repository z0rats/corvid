"""add domain age fields to ru business check

Revision ID: 39281ce75fc7
Revises: d2b7dbe28970
Create Date: 2026-08-13 19:04:56.351643

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "39281ce75fc7"
down_revision: str | None = "d2b7dbe28970"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "domain_data",
            sa.JSON(),
            nullable=True,
            comment="Optional domain-age check result (only when a website was supplied): "
            "{checked, website, domain_registration_date, wayback_first_seen_date}",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "domain_raw",
            sa.Text(),
            nullable=True,
            comment="Verbatim WHOIS/RDAP + Wayback CDX payloads for the domain-age check",
        ),
    )
    # server_default backfills existing rows - SQLite's ALTER TABLE ADD COLUMN ... NOT NULL
    # requires a server-side value, same reasoning as the pb_nalog-threshold migration.
    op.add_column(
        "ru_business_check_settings",
        sa.Column(
            "domain_age_mismatch_threshold_days",
            sa.Integer(),
            nullable=False,
            server_default="180",
            comment="Gap (days) between a company's ЕГРЮЛ registration date and its domain's "
            "evidence date at/above which the 'domain newer than company' soft flag fires",
        ),
    )


def downgrade() -> None:
    op.drop_column("ru_business_check_settings", "domain_age_mismatch_threshold_days")
    op.drop_column("ru_business_check_searches", "domain_raw")
    op.drop_column("ru_business_check_searches", "domain_data")
