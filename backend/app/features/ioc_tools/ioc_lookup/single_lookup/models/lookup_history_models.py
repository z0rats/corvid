import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SingleLookupSearch(Base):
    """A single IOC lookup search, saved once every queried service has responded"""
    __tablename__ = "single_lookup_searches"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    ioc: Mapped[str] = mapped_column(String(2000), index=True, comment="The IOC value that was looked up")
    ioc_type: Mapped[str] = mapped_column(String(20), index=True, comment="IOC type (e.g. ip, domain, hash, address)")
    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the lookup ran"
    )

    results: Mapped[list["SingleLookupResult"]] = relationship(
        back_populates="search", passive_deletes=True, order_by="SingleLookupResult.service_name"
    )


class SingleLookupResult(Base):
    """A single service's result within a single-IOC lookup search"""
    __tablename__ = "single_lookup_results"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    search_id: Mapped[int] = mapped_column(
        ForeignKey("single_lookup_searches.id", ondelete="CASCADE"), index=True, comment="Owning SingleLookupSearch.id"
    )
    service_key: Mapped[str] = mapped_column(String(100), comment="Internal identifier of the queried service")
    service_name: Mapped[str] = mapped_column(String(200), comment="Human-readable name of the queried service")
    status: Mapped[str] = mapped_column(String(20), comment="found, not_found, or error")
    summary: Mapped[str] = mapped_column(String(500), comment="Short human-readable summary of the result")
    tlp: Mapped[str] = mapped_column(String(20), comment="Traffic Light Protocol label for this result")
    data: Mapped[dict | None] = mapped_column(JSON, comment="Full raw response from the service")

    search: Mapped["SingleLookupSearch"] = relationship(back_populates="results")
