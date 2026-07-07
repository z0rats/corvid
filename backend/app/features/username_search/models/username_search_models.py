import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MaigretSearch(Base):
    """A single Maigret username search run"""
    __tablename__ = "maigret_searches"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(30), default="maigret", server_default="maigret", index=True)
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)
    total_sites_checked: Mapped[int] = mapped_column(Integer, default=0)
    found_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(1000))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))

    site_results: Mapped[list["MaigretSiteResult"]] = relationship(
        back_populates="search", passive_deletes=True, order_by="MaigretSiteResult.site_name"
    )


class MaigretSiteResult(Base):
    """A single claimed/found site result belonging to a search run.

    Only claimed (found) sites are persisted here - the ~thousands of
    not-found/error checks per run are streamed live but not stored,
    matching what's actually useful to revisit later.
    """
    __tablename__ = "maigret_site_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("maigret_searches.id", ondelete="CASCADE"), index=True)
    site_name: Mapped[str] = mapped_column(String(200))
    url_user: Mapped[str] = mapped_column(String(2000))
    http_status: Mapped[int | None] = mapped_column(Integer)
    extra: Mapped[dict | None] = mapped_column(JSON)
    """Source-specific extras not worth their own columns (e.g. social-analyzer's match rate/title)."""

    search: Mapped["MaigretSearch"] = relationship(back_populates="site_results")
