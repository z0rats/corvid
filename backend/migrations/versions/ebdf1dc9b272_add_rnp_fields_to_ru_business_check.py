"""add rnp fields to ru business check

Revision ID: ebdf1dc9b272
Revises: 39281ce75fc7
Create Date: 2026-08-13 20:52:03.154706

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ebdf1dc9b272"
down_revision: str | None = "39281ce75fc7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "rnp_data",
            sa.JSON(),
            nullable=True,
            comment="РНП (реестр недобросовестных поставщиков) check result: {checked, "
            "entries: [{registry_number, law, name, inn, included_date, updated_date, "
            "planned_exclusion_date, status, eruz_number, detail_url}]}",
        ),
    )
    op.add_column(
        "ru_business_check_searches",
        sa.Column(
            "rnp_raw",
            sa.Text(),
            nullable=True,
            comment="Verbatim RSS payload as received from zakupki.gov.ru",
        ),
    )


def downgrade() -> None:
    op.drop_column("ru_business_check_searches", "rnp_raw")
    op.drop_column("ru_business_check_searches", "rnp_data")
