from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import PypiVersionCheckMixin, TimestampMixin

TIMEOUT_SECONDS_DEFAULT = 0
TOP_SITES_COUNT_DEFAULT = 0  # 0 = scan all sites, no cap


class SocialAnalyzerConfig(Base, PypiVersionCheckMixin, TimestampMixin):
    """Single-row configuration for the social-analyzer username search source"""

    __tablename__ = "social_analyzer_config"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=TIMEOUT_SECONDS_DEFAULT,
        comment="Per-site check timeout, in seconds (0 = no timeout)",
    )
    top_sites_count: Mapped[int] = mapped_column(
        Integer,
        default=TOP_SITES_COUNT_DEFAULT,
        comment="Max number of top sites to scan (0 = scan all sites)",
    )
