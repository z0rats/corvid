import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class BlacklistSource(str, Enum):
    OFAC = "OFAC"
    SCAMSNIFFER = "SCAMSNIFFER"


class BlacklistedAddress(Base):
    """Address reputation entry sourced from open, no-key data feeds (OFAC SDN, ScamSniffer)."""
    __tablename__ = "blacklisted_addresses"
    __table_args__ = (
        UniqueConstraint("address", "source", name="uq_blacklist_address_source"),
        CheckConstraint("source IN ('OFAC', 'SCAMSNIFFER')", name="ck_blacklisted_addresses_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    address: Mapped[str] = mapped_column(String(128), index=True, comment="Blockchain address or IOC value")
    source: Mapped[str] = mapped_column(
        String(20), index=True, comment="Feed this entry came from: 'OFAC' or 'SCAMSNIFFER'"
    )
    chain: Mapped[str | None] = mapped_column(String(20), comment="Blockchain the address belongs to, if known")
    label: Mapped[str | None] = mapped_column(String(255), comment="Short human-readable label for the entry")
    entity_name: Mapped[str | None] = mapped_column(String(255), comment="Sanctioned/flagged entity name, if known")
    details: Mapped[dict | None] = mapped_column(JSON, comment="Raw source-specific feed record")
    is_active: Mapped[bool] = mapped_column(default=True, comment="Whether the entry is still present in the source feed")
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When this entry was first ingested"
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When this entry was last seen in a feed refresh"
    )
