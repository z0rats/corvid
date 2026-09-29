"""add registry dump tables (disqualified persons, ЦБ warning list, OFAC SDN) for ru_business_check

Revision ID: b4d92e6a1c58
Revises: a3c81f52d9e7
Create Date: 2026-09-28 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4d92e6a1c58"
down_revision: str | None = "a3c81f52d9e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ru_business_check_disqualified_records",
        sa.Column("id", sa.Integer(), nullable=False, comment="Surrogate primary key"),
        sa.Column(
            "record_number",
            sa.String(length=20),
            nullable=False,
            comment="Register record number (CSV column G1)",
        ),
        sa.Column(
            "full_name",
            sa.String(length=300),
            nullable=False,
            comment="ФИО normalized for matching: upper case, ё->е, single spaces (column G2)",
        ),
        sa.Column(
            "org_name",
            sa.String(length=500),
            nullable=True,
            comment="Organization the person was disqualified in (column G5)",
        ),
        sa.Column(
            "org_inn",
            sa.String(length=12),
            nullable=True,
            comment="That organization's ИНН (column G6) - only ~36% of records carry it",
        ),
        sa.Column(
            "position",
            sa.String(length=300),
            nullable=True,
            comment="Position held (column G7)",
        ),
        sa.Column(
            "article", sa.String(length=300), nullable=True, comment="КоАП article (column G8)"
        ),
        sa.Column(
            "term",
            sa.String(length=50),
            nullable=True,
            comment="Disqualification term as written, e.g. '2 г 0 м 0 д' (column G12)",
        ),
        sa.Column(
            "start_date", sa.Date(), nullable=False, comment="Disqualification start (column G13)"
        ),
        sa.Column(
            "end_date", sa.Date(), nullable=False, comment="Disqualification end (column G14)"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ru_business_check_disqualified_records_full_name"),
        "ru_business_check_disqualified_records",
        ["full_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ru_business_check_disqualified_records_org_inn"),
        "ru_business_check_disqualified_records",
        ["org_inn"],
        unique=False,
    )
    op.create_table(
        "ru_business_check_cbr_warning_records",
        sa.Column("id", sa.Integer(), nullable=False, comment="Surrogate primary key"),
        sa.Column("cbr_id", sa.Integer(), nullable=False, comment="The list's own entry id (`Id`)"),
        sa.Column(
            "inn",
            sa.String(length=10),
            nullable=False,
            comment="10-digit ИНН of the listed legal entity",
        ),
        sa.Column("name", sa.String(length=500), nullable=True, comment="Listed name (`Name`)"),
        sa.Column(
            "sign",
            sa.String(length=500),
            nullable=True,
            comment="The regulator's stated sign of illegal activity (`Sign`)",
        ),
        sa.Column(
            "listed_at",
            sa.Date(),
            nullable=True,
            comment="Date the entry was added to the list (`DT`)",
        ),
        sa.Column(
            "closed",
            sa.Boolean(),
            nullable=False,
            comment="The regulator marks the organization as liquidated (`Closed`)",
        ),
        sa.Column("comment", sa.String(length=1000), nullable=True, comment="Regulator's note"),
        sa.Column(
            "is_clone",
            sa.Boolean(),
            nullable=False,
            comment="Note says the entry misuses a legitimate market participant's data: the "
            "ИНН owner is the impersonated party, not the offender",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ru_business_check_cbr_warning_records_inn"),
        "ru_business_check_cbr_warning_records",
        ["inn"],
        unique=False,
    )
    op.create_table(
        "ru_business_check_ofac_sdn_records",
        sa.Column("id", sa.Integer(), nullable=False, comment="Surrogate primary key"),
        sa.Column(
            "ent_num", sa.Integer(), nullable=False, comment="The SDN list's own entry number"
        ),
        sa.Column(
            "inn",
            sa.String(length=12),
            nullable=False,
            comment="Russian ИНН from the entry's remarks (10 digits = legal entity, 12 = person)",
        ),
        sa.Column(
            "name",
            sa.String(length=500),
            nullable=False,
            comment="SDN name (transliterated)",
        ),
        sa.Column(
            "kind",
            sa.String(length=20),
            nullable=False,
            comment="'entity' (SDN type -0-) or 'individual'",
        ),
        sa.Column(
            "programs",
            sa.String(length=500),
            nullable=True,
            comment="Sanctions programs, e.g. 'UKRAINE-EO13661] [RUSSIA-EO14024'",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ru_business_check_ofac_sdn_records_inn"),
        "ru_business_check_ofac_sdn_records",
        ["inn"],
        unique=False,
    )
    op.create_table(
        "ru_business_check_registry_dumps",
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
            comment="Dump source id, e.g. 'disqualified'",
        ),
        sa.Column(
            "dump_date",
            sa.Date(),
            nullable=False,
            comment="Date of the published dataset version (the publisher's meta.csv), or the "
            "download date for a list published without one",
        ),
        sa.Column(
            "valid_until",
            sa.Date(),
            nullable=True,
            comment="The publisher's stated validity end (meta.csv `valid`), if given",
        ),
        sa.Column(
            "row_count", sa.Integer(), nullable=False, comment="Rows loaded from that version"
        ),
        sa.Column(
            "url",
            sa.String(length=500),
            nullable=False,
            comment="Where this version was downloaded",
        ),
        sa.Column(
            "refreshed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="When this instance last loaded the dump",
        ),
        sa.PrimaryKeyConstraint("source"),
    )


def downgrade() -> None:
    op.drop_table("ru_business_check_registry_dumps")
    op.drop_index(
        op.f("ix_ru_business_check_ofac_sdn_records_inn"),
        table_name="ru_business_check_ofac_sdn_records",
    )
    op.drop_table("ru_business_check_ofac_sdn_records")
    op.drop_index(
        op.f("ix_ru_business_check_cbr_warning_records_inn"),
        table_name="ru_business_check_cbr_warning_records",
    )
    op.drop_table("ru_business_check_cbr_warning_records")
    op.drop_index(
        op.f("ix_ru_business_check_disqualified_records_org_inn"),
        table_name="ru_business_check_disqualified_records",
    )
    op.drop_index(
        op.f("ix_ru_business_check_disqualified_records_full_name"),
        table_name="ru_business_check_disqualified_records",
    )
    op.drop_table("ru_business_check_disqualified_records")
