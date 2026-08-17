"""add fedsfm fields to ru business check

Revision ID: d2b7dbe28970
Revises: e99c7cd3359e
Create Date: 2026-08-13 18:44:11.558543

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2b7dbe28970"
down_revision: str | None = "e99c7cd3359e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "fedsfm_result",
            sa.JSON(),
            nullable=True,
            comment="ФедСФМ (терроризм/финансирование ОМУ) check result: {checked, matched, "
            "requires_manual_review, matches: [...]}",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "fedsfm_raw",
            sa.Text(),
            nullable=True,
            comment="Verbatim ФедСФМ payload as received from fedsfm.ru/TerroristSearch",
        ),
    )


def downgrade() -> None:
    op.drop_column("ru_business_check_searches", "fedsfm_raw")
    op.drop_column("ru_business_check_searches", "fedsfm_result")
