from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import TimestampMixin


class CTIProfileSettings(Base, TimestampMixin):
    """Database model for CTI profile settings"""

    __tablename__ = 'cti_profile_settings'

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    settings_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, comment="Free-form CTI profile config (sectors, regions, keywords, etc.)"
    )
