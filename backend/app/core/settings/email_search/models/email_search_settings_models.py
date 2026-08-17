from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import PypiVersionCheckMixin, TimestampMixin
from app.features.email_search.config.defaults import (
    ENABLE_HEADLESS_CHECKS_DEFAULT,
    ENABLE_SMTP_CHECKS_DEFAULT,
    MAX_CONCURRENCY_DEFAULT,
    TIMEOUT_SECONDS_DEFAULT,
    USE_TOR_DEFAULT,
)


class EmailSearchConfig(Base, PypiVersionCheckMixin, TimestampMixin):
    """Single-row configuration for the mailcat email search feature"""

    __tablename__ = "email_search_config"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, default=TIMEOUT_SECONDS_DEFAULT, comment="Per-provider check timeout, in seconds"
    )
    max_concurrency: Mapped[int] = mapped_column(
        Integer,
        default=MAX_CONCURRENCY_DEFAULT,
        comment="Max number of providers checked in parallel",
    )
    proxy_url: Mapped[str | None] = mapped_column(
        String(500), comment="Optional HTTP(S) proxy URL for provider checks"
    )
    use_tor: Mapped[bool] = mapped_column(
        Boolean, default=USE_TOR_DEFAULT, comment="Whether to route checks through Tor"
    )
    enable_smtp_checks: Mapped[bool] = mapped_column(
        Boolean,
        default=ENABLE_SMTP_CHECKS_DEFAULT,
        comment="Whether to run SMTP-based mailbox existence checks",
    )
    enable_headless_checks: Mapped[bool] = mapped_column(
        Boolean,
        default=ENABLE_HEADLESS_CHECKS_DEFAULT,
        comment="Whether to run headless-browser-based provider checks",
    )
