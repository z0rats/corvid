import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class BlacklistSource(str, Enum):
    OFAC = "OFAC"
    SCAMSNIFFER = "SCAMSNIFFER"


class BlacklistedAddress(Base):
    """Address reputation entry sourced from open, no-key data feeds (OFAC SDN, ScamSniffer)."""
    __tablename__ = "blacklisted_addresses"
    __table_args__ = (UniqueConstraint("address", "source", name="uq_blacklist_address_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(128), index=True)
    source: Mapped[str] = mapped_column(String(20), index=True)
    chain: Mapped[str | None] = mapped_column(String(20))
    label: Mapped[str | None] = mapped_column(String(255))
    entity_name: Mapped[str | None] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)
    first_seen_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
