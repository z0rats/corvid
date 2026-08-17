"""add opensanctions to blacklist source check constraint

Revision ID: de923d7047e4
Revises: 537d93424e1d
Create Date: 2026-08-11 21:30:32.210284

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de923d7047e4"
down_revision: str | None = "537d93424e1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("blacklisted_addresses") as batch_op:
        batch_op.drop_constraint("ck_blacklisted_addresses_source", type_="check")
        batch_op.create_check_constraint(
            "ck_blacklisted_addresses_source",
            "source IN ('OFAC', 'SCAMSNIFFER', 'OPENSANCTIONS')",
        )


def downgrade() -> None:
    with op.batch_alter_table("blacklisted_addresses") as batch_op:
        batch_op.drop_constraint("ck_blacklisted_addresses_source", type_="check")
        batch_op.create_check_constraint(
            "ck_blacklisted_addresses_source",
            "source IN ('OFAC', 'SCAMSNIFFER')",
        )
