from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.settings.general.config.default_settings import (
    get_default_darkmode,
    get_default_font,
    FONT_MAX_LENGTH
)


class GeneralSettings(Base):
    """Database model for general application settings"""
    __tablename__ = 'general_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    darkmode: Mapped[bool] = mapped_column(default=get_default_darkmode())
    font: Mapped[str] = mapped_column(String(FONT_MAX_LENGTH), default=get_default_font())
