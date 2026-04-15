import datetime
import json
from typing import Any

from sqlalchemy import Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class CTIProfileSettings(Base):
    """Database model for CTI profile settings"""

    __tablename__ = 'cti_profile_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    settings_data: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def get_settings_dict(self) -> dict[str, Any]:
        """Parse and return settings as dictionary"""
        try:
            return json.loads(self.settings_data)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_settings_dict(self, settings: dict[str, Any]) -> None:
        """Set settings from dictionary"""
        self.settings_data = json.dumps(settings)
