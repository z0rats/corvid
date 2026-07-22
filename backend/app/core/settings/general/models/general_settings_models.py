from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.settings.general.config.default_settings import (
    get_default_darkmode,
    get_default_language,
    get_default_auto_open_on_single_match,
    get_default_start_screen,
    get_default_always_tiles,
    LANGUAGE_MAX_LENGTH,
    START_SCREEN_MAX_LENGTH
)


class GeneralSettings(Base):
    """Database model for general application settings"""
    __tablename__ = 'general_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    darkmode: Mapped[bool] = mapped_column(default=get_default_darkmode())
    language: Mapped[str] = mapped_column(String(LANGUAGE_MAX_LENGTH), default=get_default_language())
    auto_open_on_single_match: Mapped[bool] = mapped_column(default=get_default_auto_open_on_single_match())
    start_screen: Mapped[str] = mapped_column(String(START_SCREEN_MAX_LENGTH), default=get_default_start_screen())
    always_tiles: Mapped[bool] = mapped_column(default=get_default_always_tiles())
