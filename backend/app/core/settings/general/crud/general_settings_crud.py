"""General settings database operations"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.settings.general.models.general_settings_models import GeneralSettings
from app.core.settings.general.config.default_settings import (
    get_default_darkmode,
    get_default_language,
    get_default_auto_open_on_single_match,
    get_default_start_screen,
    get_default_always_tiles
)


async def get_general_settings_by_id(db: AsyncSession, settings_id: int) -> GeneralSettings | None:
    """Retrieve general settings by ID"""
    stmt = select(GeneralSettings).where(GeneralSettings.id == settings_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_first_general_settings(db: AsyncSession) -> GeneralSettings | None:
    """Retrieve the first general settings record"""
    stmt = select(GeneralSettings).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_general_settings(
    db: AsyncSession,
    darkmode: bool | None = None,
    language: str | None = None,
    auto_open_on_single_match: bool | None = None,
    start_screen: str | None = None,
    always_tiles: bool | None = None
) -> GeneralSettings:
    """Create new general settings record"""
    settings = GeneralSettings(
        darkmode=darkmode if darkmode is not None else get_default_darkmode(),
        language=language if language is not None else get_default_language(),
        auto_open_on_single_match=(
            auto_open_on_single_match if auto_open_on_single_match is not None
            else get_default_auto_open_on_single_match()
        ),
        start_screen=start_screen if start_screen is not None else get_default_start_screen(),
        always_tiles=always_tiles if always_tiles is not None else get_default_always_tiles()
    )
    db.add(settings)
    await db.flush()
    return settings


async def update_general_settings_darkmode(
    db: AsyncSession,
    settings: GeneralSettings,
    darkmode: bool
) -> GeneralSettings:
    """Update darkmode setting for existing record"""
    settings.darkmode = darkmode
    await db.flush()
    return settings


async def update_general_settings_language(
    db: AsyncSession,
    settings: GeneralSettings,
    language: str
) -> GeneralSettings:
    """Update language setting for existing record"""
    settings.language = language
    await db.flush()
    return settings


async def update_general_settings_all(
    db: AsyncSession,
    settings: GeneralSettings,
    darkmode: bool | None = None,
    language: str | None = None
) -> GeneralSettings:
    """Update multiple settings fields for existing record"""
    if darkmode is not None:
        settings.darkmode = darkmode
    if language is not None:
        settings.language = language
    await db.flush()
    return settings


async def update_general_settings_command_palette(
    db: AsyncSession,
    settings: GeneralSettings,
    auto_open_on_single_match: bool | None = None,
    start_screen: str | None = None,
    always_tiles: bool | None = None
) -> GeneralSettings:
    """Update command palette settings fields for existing record"""
    if auto_open_on_single_match is not None:
        settings.auto_open_on_single_match = auto_open_on_single_match
    if start_screen is not None:
        settings.start_screen = start_screen
    if always_tiles is not None:
        settings.always_tiles = always_tiles
    await db.flush()
    return settings


async def delete_general_settings(db: AsyncSession, settings: GeneralSettings) -> None:
    """Delete general settings record"""
    await db.delete(settings)
    await db.flush()
