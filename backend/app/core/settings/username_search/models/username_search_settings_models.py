import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.features.username_search.config.maigret_config import (
    AUTO_UPDATE_DB_ENABLED_DEFAULT,
    AUTO_UPDATE_INTERVAL_HOURS_DEFAULT,
    MAX_CONCURRENCY_DEFAULT,
    TIMEOUT_SECONDS_DEFAULT,
    TOP_SITES_COUNT_DEFAULT,
)


class UsernameSearchConfig(Base):
    """Single-row configuration for the Maigret username search feature"""
    __tablename__ = "username_search_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=TIMEOUT_SECONDS_DEFAULT)
    max_concurrency: Mapped[int] = mapped_column(Integer, default=MAX_CONCURRENCY_DEFAULT)
    top_sites_count: Mapped[int] = mapped_column(Integer, default=TOP_SITES_COUNT_DEFAULT)
    proxy_url: Mapped[str | None] = mapped_column(String(500))
    auto_update_db_enabled: Mapped[bool] = mapped_column(Boolean, default=AUTO_UPDATE_DB_ENABLED_DEFAULT)
    auto_update_interval_hours: Mapped[int] = mapped_column(Integer, default=AUTO_UPDATE_INTERVAL_HOURS_DEFAULT)
    db_last_updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    db_site_count: Mapped[int] = mapped_column(Integer, default=0)
    latest_pypi_version: Mapped[str | None] = mapped_column(String(50))
    pypi_checked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
