import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MaigretSearch(Base):
    """A single Maigret username search run"""

    __tablename__ = "maigret_searches"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'cancelled', 'failed')",
            name="ck_maigret_searches_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    username: Mapped[str] = mapped_column(String(100), index=True, comment="Username searched")
    source: Mapped[str] = mapped_column(
        String(30),
        default="maigret",
        server_default="maigret",
        index=True,
        comment="Which tool produced this run: 'maigret' or 'social_analyzer'",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="running",
        index=True,
        comment="running, completed, cancelled, or failed",
    )
    total_sites_checked: Mapped[int] = mapped_column(
        Integer, default=0, comment="Sites checked so far"
    )
    found_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Sites where the username was claimed/found"
    )
    error_message: Mapped[str | None] = mapped_column(
        String(1000), comment="Error detail if status is failed"
    )
    tags: Mapped[list[str] | None] = mapped_column(
        JSON, comment="Maigret category tags matched for this username"
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the search run started"
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the search run finished, if it has"
    )

    site_results: Mapped[list[MaigretSiteResult]] = relationship(
        back_populates="search", passive_deletes=True, order_by="MaigretSiteResult.site_name"
    )


class MaigretSiteResult(Base):
    """A single claimed/found site result belonging to a search run.

    Only claimed (found) sites are persisted here - the ~thousands of
    not-found/error checks per run are streamed live but not stored,
    matching what's actually useful to revisit later.
    """

    __tablename__ = "maigret_site_results"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    search_id: Mapped[int] = mapped_column(
        ForeignKey("maigret_searches.id", ondelete="CASCADE"),
        index=True,
        comment="Owning MaigretSearch.id",
    )
    site_name: Mapped[str] = mapped_column(
        String(200), comment="Site where the username was claimed/found"
    )
    url_user: Mapped[str] = mapped_column(String(2000), comment="Direct URL to the found profile")
    http_status: Mapped[int | None] = mapped_column(
        Integer, comment="HTTP status code returned by the site check"
    )
    extra: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "Source-specific extras not worth their own columns (e.g. "
            "social-analyzer's match rate/title)"
        ),
    )

    search: Mapped[MaigretSearch] = relationship(back_populates="site_results")
