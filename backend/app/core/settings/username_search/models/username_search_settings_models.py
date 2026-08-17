import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import PypiVersionCheckMixin, TimestampMixin
from app.features.username_search.config.maigret_config import (
    AUTO_UPDATE_DB_ENABLED_DEFAULT,
    AUTO_UPDATE_INTERVAL_HOURS_DEFAULT,
    MAX_CONCURRENCY_DEFAULT,
    TIMEOUT_SECONDS_DEFAULT,
    TOP_SITES_COUNT_DEFAULT,
)


class UsernameSearchConfig(Base, PypiVersionCheckMixin, TimestampMixin):
    """Single-row configuration for the Maigret username search feature"""

    __tablename__ = "username_search_config"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, default=TIMEOUT_SECONDS_DEFAULT, comment="Per-site check timeout, in seconds"
    )
    max_concurrency: Mapped[int] = mapped_column(
        Integer, default=MAX_CONCURRENCY_DEFAULT, comment="Max number of sites checked in parallel"
    )
    top_sites_count: Mapped[int] = mapped_column(
        Integer,
        default=TOP_SITES_COUNT_DEFAULT,
        comment="Max number of top sites to scan (0 = scan all sites)",
    )
    proxy_url: Mapped[str | None] = mapped_column(
        String(500), comment="Optional HTTP(S) proxy URL for site checks"
    )
    auto_update_db_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=AUTO_UPDATE_DB_ENABLED_DEFAULT,
        comment="Whether Maigret's site database is refreshed automatically on a schedule",
    )
    auto_update_interval_hours: Mapped[int] = mapped_column(
        Integer,
        default=AUTO_UPDATE_INTERVAL_HOURS_DEFAULT,
        comment="Hours between automatic site-database refreshes",
    )
    db_last_updated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), comment="When the Maigret site database was last refreshed"
    )
    db_site_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Number of sites in the current Maigret site database"
    )
