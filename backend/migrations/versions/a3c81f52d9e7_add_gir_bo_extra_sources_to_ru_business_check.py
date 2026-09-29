"""add extra_data/extra_raw/raw_sha256 and ГИР БО thresholds to ru_business_check

Revision ID: a3c81f52d9e7
Revises: 6f94ea21edb9
Create Date: 2026-09-28 14:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c81f52d9e7"
down_revision: str | None = "6f94ea21edb9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "extra_data",
            sa.JSON(),
            nullable=True,
            comment="Parsed results of sources added after the dedicated *_data columns, keyed "
            "by source id (e.g. {gir_bo: {...}}) - new sources land here instead of costing "
            "two columns and a migration each, see docs/adr/0014-*.md",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "extra_raw",
            sa.JSON(),
            nullable=True,
            comment="Verbatim payloads for extra_data's sources, keyed the same way: "
            "{source: text}",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "raw_sha256",
            sa.JSON(),
            nullable=True,
            comment="SHA-256 of each source's verbatim payload as captured at scan time, "
            "keyed by source id: {source: hex digest}; sources with no payload are omitted",
        ),
    )
    # server_default backfills the existing singleton row - SQLite's ALTER TABLE ADD COLUMN
    # ... NOT NULL requires a server-side value, same reasoning as the earlier threshold
    # migrations.
    op.add_column(
        "ru_business_check_settings",
        sa.Column(
            "equity_ratio_threshold",
            sa.Float(),
            nullable=False,
            server_default="0.1",
            comment="ГИР БО equity ratio (строка 1300 / строка 1600) below which the soft "
            "'low equity ratio' flag fires",
        ),
    )
    op.add_column(
        "ru_business_check_settings",
        sa.Column(
            "current_ratio_threshold",
            sa.Float(),
            nullable=False,
            server_default="1.0",
            comment="ГИР БО current ratio (строка 1200 / строка 1500) below which the soft "
            "'low current liquidity' flag fires",
        ),
    )
    op.add_column(
        "ru_business_check_settings",
        sa.Column(
            "revenue_drop_threshold",
            sa.Float(),
            nullable=False,
            server_default="0.5",
            comment="Year-over-year ГИР БО revenue drop (0-1 fraction) above which the soft "
            "'revenue drop' flag fires",
        ),
    )


def downgrade() -> None:
    op.drop_column("ru_business_check_settings", "revenue_drop_threshold")
    op.drop_column("ru_business_check_settings", "current_ratio_threshold")
    op.drop_column("ru_business_check_settings", "equity_ratio_threshold")
    op.drop_column("ru_business_check_searches", "raw_sha256")
    op.drop_column("ru_business_check_searches", "extra_raw")
    op.drop_column("ru_business_check_searches", "extra_data")
