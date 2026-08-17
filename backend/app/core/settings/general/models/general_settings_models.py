from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models.mixins import TimestampMixin
from app.core.settings.general.config.default_settings import (
    LANGUAGE_MAX_LENGTH,
    START_SCREEN_MAX_LENGTH,
    get_default_always_tiles,
    get_default_auto_open_on_single_match,
    get_default_darkmode,
    get_default_language,
    get_default_start_screen,
)


class GeneralSettings(Base, TimestampMixin):
    """Database model for general application settings"""

    __tablename__ = "general_settings"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    darkmode: Mapped[bool] = mapped_column(
        default=get_default_darkmode(), comment="Whether the UI theme is dark mode"
    )
    language: Mapped[str] = mapped_column(
        String(LANGUAGE_MAX_LENGTH),
        default=get_default_language(),
        comment="UI language code (e.g. 'en', 'ru')",
    )
    auto_open_on_single_match: Mapped[bool] = mapped_column(
        default=get_default_auto_open_on_single_match(),
        comment="Whether to auto-open the result when a search returns exactly one match",
    )
    start_screen: Mapped[str] = mapped_column(
        String(START_SCREEN_MAX_LENGTH),
        default=get_default_start_screen(),
        comment="Which screen the app opens on startup",
    )
    always_tiles: Mapped[bool] = mapped_column(
        default=get_default_always_tiles(),
        comment="Whether to always use tile layout instead of tabs",
    )
