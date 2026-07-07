import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

TIMEOUT_SECONDS_DEFAULT = 0
TOP_SITES_COUNT_DEFAULT = 0  # 0 = scan all sites, no cap


class SocialAnalyzerConfig(Base):
    """Single-row configuration for the social-analyzer username search source"""
    __tablename__ = "social_analyzer_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=TIMEOUT_SECONDS_DEFAULT)
    top_sites_count: Mapped[int] = mapped_column(Integer, default=TOP_SITES_COUNT_DEFAULT)
    latest_pypi_version: Mapped[str | None] = mapped_column(String(50))
    pypi_checked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
