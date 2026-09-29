"""rename registry dumps table and add sanctions entries

Revision ID: 43f3a99819ae
Revises: 8d9be91ec8d9
Create Date: 2026-09-29 11:28:52.369715

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "43f3a99819ae"
down_revision: str | None = "8d9be91ec8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The registry-dump provenance table was promoted from ru_business_check to core
    # (app.core.registry_dumps) so a second, unrelated feature (sanctions_search) could reuse
    # it without depending on ru_business_check's internals - see docs/adr/0017-*.md.
    op.rename_table("ru_business_check_registry_dumps", "registry_dumps")

    op.create_table(
        "sanctions_entries",
        sa.Column("id", sa.Integer(), nullable=False, comment="Surrogate primary key"),
        sa.Column(
            "opensanctions_id",
            sa.String(length=64),
            nullable=False,
            comment="OpenSanctions' own entity id (CSV `id`), e.g. 'NK-xxxx'",
        ),
        sa.Column(
            "schema",
            sa.String(length=30),
            nullable=False,
            comment="OpenSanctions entity schema (CSV `schema`): Person, Organization, "
            "Vessel, Airplane, Company, Security, LegalEntity, CryptoWallet, ...",
        ),
        sa.Column(
            "name",
            sa.String(length=500),
            nullable=False,
            comment="Primary/caption name (CSV `name`)",
        ),
        sa.Column(
            "aliases",
            sa.JSON(),
            nullable=False,
            comment="Alternate names/aka's (CSV `aliases`, ;-separated), as a list",
        ),
        sa.Column(
            "countries",
            sa.JSON(),
            nullable=False,
            comment="Country/jurisdiction codes (CSV `countries`), as a list",
        ),
        sa.Column(
            "programs",
            sa.JSON(),
            nullable=False,
            comment="Sanctions program ids (CSV `program_ids`), as a list",
        ),
        sa.Column(
            "sanctions",
            sa.Text(),
            nullable=True,
            comment="Free-text sanction designation description(s) (CSV `sanctions`)",
        ),
        sa.Column(
            "first_seen",
            sa.Date(),
            nullable=True,
            comment="First time OpenSanctions observed this entity (CSV `first_seen`)",
        ),
        sa.Column(
            "last_seen",
            sa.Date(),
            nullable=True,
            comment="Last time OpenSanctions confirmed this entity (CSV `last_seen`)",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sanctions_entries_opensanctions_id"),
        "sanctions_entries",
        ["opensanctions_id"],
        unique=False,
    )
    op.create_index(op.f("ix_sanctions_entries_name"), "sanctions_entries", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sanctions_entries_name"), table_name="sanctions_entries")
    op.drop_index(op.f("ix_sanctions_entries_opensanctions_id"), table_name="sanctions_entries")
    op.drop_table("sanctions_entries")
    op.rename_table("registry_dumps", "ru_business_check_registry_dumps")
