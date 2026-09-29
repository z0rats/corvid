import datetime

from sqlalchemy import JSON, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SanctionsEntry(Base):
    """One row of OpenSanctions' cleaned `us_ofac_sdn` targets CSV. Replaced wholesale on each
    refresh (see `service/sanctions_search_service.py`) - no TimestampMixin, this is a
    bulk-replaced dump table, not a row-lifecycle one, same as ru_business_check's
    OfacSdnRecord/DisqualifiedRecord (see docs/adr/0017-*.md for why this is a separate table
    from that ИНН-exact OFAC mirror rather than sharing it)."""

    __tablename__ = "sanctions_entries"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    opensanctions_id: Mapped[str] = mapped_column(
        String(64), index=True, comment="OpenSanctions' own entity id (CSV `id`), e.g. 'NK-xxxx'"
    )
    schema: Mapped[str] = mapped_column(
        String(30),
        comment="OpenSanctions entity schema (CSV `schema`): Person, Organization, Vessel, "
        "Airplane, Company, Security, LegalEntity, CryptoWallet, ...",
    )
    name: Mapped[str] = mapped_column(
        String(500), index=True, comment="Primary/caption name (CSV `name`)"
    )
    aliases: Mapped[list] = mapped_column(
        JSON, comment="Alternate names/aka's (CSV `aliases`, ;-separated), as a list"
    )
    countries: Mapped[list] = mapped_column(
        JSON, comment="Country/jurisdiction codes (CSV `countries`), as a list"
    )
    programs: Mapped[list] = mapped_column(
        JSON, comment="Sanctions program ids (CSV `program_ids`), as a list"
    )
    sanctions: Mapped[str | None] = mapped_column(
        Text, comment="Free-text sanction designation description(s) (CSV `sanctions`)"
    )
    first_seen: Mapped[datetime.date | None] = mapped_column(
        Date, comment="First time OpenSanctions observed this entity (CSV `first_seen`)"
    )
    last_seen: Mapped[datetime.date | None] = mapped_column(
        Date, comment="Last time OpenSanctions confirmed this entity (CSV `last_seen`)"
    )
