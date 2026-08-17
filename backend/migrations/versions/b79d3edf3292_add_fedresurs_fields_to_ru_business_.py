"""add fedresurs fields to ru_business_check

Revision ID: b79d3edf3292
Revises: 156f6418a311
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b79d3edf3292"
down_revision: str | None = "156f6418a311"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "fedresurs_data",
            sa.JSON(),
            nullable=True,
            comment="Bankruptcy check result: {checked, found, status_text, "
            "is_active_bankruptcy, profile_url}",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "fedresurs_raw",
            sa.Text(),
            nullable=True,
            comment="Verbatim bankruptcy search-result payload as received from fedresurs.ru",
        ),
    )


def downgrade() -> None:
    op.drop_column("ru_business_check_searches", "fedresurs_raw")
    op.drop_column("ru_business_check_searches", "fedresurs_data")
