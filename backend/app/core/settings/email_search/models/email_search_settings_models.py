import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.features.email_search.config.mailcat_config import (
    ENABLE_HEADLESS_CHECKS_DEFAULT,
    ENABLE_SMTP_CHECKS_DEFAULT,
    MAX_CONCURRENCY_DEFAULT,
    TIMEOUT_SECONDS_DEFAULT,
    USE_TOR_DEFAULT,
)


class EmailSearchConfig(Base):
    """Single-row configuration for the mailcat email search feature"""
    __tablename__ = "email_search_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=TIMEOUT_SECONDS_DEFAULT)
    max_concurrency: Mapped[int] = mapped_column(Integer, default=MAX_CONCURRENCY_DEFAULT)
    proxy_url: Mapped[str | None] = mapped_column(String(500))
    use_tor: Mapped[bool] = mapped_column(Boolean, default=USE_TOR_DEFAULT)
    enable_smtp_checks: Mapped[bool] = mapped_column(Boolean, default=ENABLE_SMTP_CHECKS_DEFAULT)
    enable_headless_checks: Mapped[bool] = mapped_column(Boolean, default=ENABLE_HEADLESS_CHECKS_DEFAULT)
    latest_pypi_version: Mapped[str | None] = mapped_column(String(50))
    pypi_checked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
