import datetime

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegistryDump(Base):
    """Provenance of a locally cached registry dump - one row per source. Shared by every
    feature that periodically replaces a locally cached copy of a published list (ЕФРСБ/ФНС
    disqualified-persons dump, ЦБ warning list, OFAC SDN, ...) - see `app/core/registry_dumps/`."""

    __tablename__ = "registry_dumps"

    source: Mapped[str] = mapped_column(
        String(50), primary_key=True, comment="Dump source id, e.g. 'disqualified'"
    )
    dump_date: Mapped[datetime.date] = mapped_column(
        Date,
        comment="Date of the published dataset version (the publisher's meta.csv), or the "
        "download date for a list published without one",
    )
    valid_until: Mapped[datetime.date | None] = mapped_column(
        Date, comment="The publisher's stated validity end (meta.csv `valid`), if given"
    )
    row_count: Mapped[int] = mapped_column(Integer, comment="Rows loaded from that version")
    url: Mapped[str] = mapped_column(String(500), comment="Where this version was downloaded")
    refreshed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), comment="When this instance last loaded the dump"
    )
