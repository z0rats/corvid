import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SingleLookupSearch(Base):
    """A single IOC lookup search, saved once every queried service has responded"""
    __tablename__ = "single_lookup_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    ioc: Mapped[str] = mapped_column(String(2000), index=True)
    ioc_type: Mapped[str] = mapped_column(String(20), index=True)
    searched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    results: Mapped[list["SingleLookupResult"]] = relationship(
        back_populates="search", passive_deletes=True, order_by="SingleLookupResult.service_name"
    )


class SingleLookupResult(Base):
    """A single service's result within a single-IOC lookup search"""
    __tablename__ = "single_lookup_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("single_lookup_searches.id", ondelete="CASCADE"), index=True)
    service_key: Mapped[str] = mapped_column(String(100))
    service_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))  # found, not_found, or error
    summary: Mapped[str] = mapped_column(String(500))
    tlp: Mapped[str] = mapped_column(String(20))
    data: Mapped[dict | None] = mapped_column(JSON)

    search: Mapped["SingleLookupSearch"] = relationship(back_populates="results")
