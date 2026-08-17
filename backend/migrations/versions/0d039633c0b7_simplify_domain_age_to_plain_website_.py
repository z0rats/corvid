"""simplify domain age to plain website field

Revision ID: 0d039633c0b7
Revises: ebdf1dc9b272
Create Date: 2026-08-14 16:36:02.455623

The automated WHOIS/RDAP + Wayback domain-age check was removed in favor of a plain
user-supplied website field, displayed with a link out to domain_finder's own (richer)
domain analysis instead of duplicating it here. `pb_nalog_data`'s `director_indicator`
field was also dropped (unreliable - manual re-verification against pb.nalog.ru's own UI
found nothing corresponding to it), but that's a JSON-blob shape change with no DDL of its
own to migrate.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d039633c0b7"
down_revision: str | None = "ebdf1dc9b272"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "website",
            sa.String(length=255),
            nullable=True,
            comment="Optional company website, user-supplied - display-only, not analyzed "
            "by this feature itself; the UI links it out to domain_finder's own "
            "WHOIS/DNS/CT analysis instead of duplicating it here",
        ),
    )
    op.drop_column("ru_business_check_searches", "domain_raw")
    op.drop_column("ru_business_check_searches", "domain_data")
    op.drop_column("ru_business_check_settings", "domain_age_mismatch_threshold_days")


def downgrade() -> None:
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
    op.drop_column("ru_business_check_searches", "website")
