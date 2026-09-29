from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import TimestampMixin
from app.features.phone_search.config.defaults import TIMEOUT_SECONDS_DEFAULT


class PhoneSearchConfig(Base, TimestampMixin):
    """Single-row configuration for the phone search feature"""

    __tablename__ = "phone_search_config"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    timeout_seconds: Mapped[int] = mapped_column(
        Integer, default=TIMEOUT_SECONDS_DEFAULT, comment="Per-provider check timeout, in seconds"
    )
    proxy_url: Mapped[str | None] = mapped_column(
        String(500), comment="Optional HTTP(S) proxy URL for provider checks"
    )
