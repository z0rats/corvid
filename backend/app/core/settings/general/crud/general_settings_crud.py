"""General settings database operations"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.general.config.default_settings import (
    get_default_always_tiles,
    get_default_auto_open_on_single_match,
    get_default_darkmode,
    get_default_language,
    get_default_start_screen,
)
from app.core.settings.general.models.general_settings_models import GeneralSettings


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
    always_tiles: bool | None = None,
) -> GeneralSettings:
    """Create the singleton general settings record (fixed id=1).

    Callers only reach this after `get_first_general_settings` found no row, but that
    check isn't atomic with the insert - a concurrent first request can win the race.
    Forcing id=1 turns that into a primary-key collision instead of a duplicate row:
    the loser's insert is rolled back via a savepoint (isolated from anything else
    pending in the caller's session) and it just returns the winner's row instead.
    """
    settings = GeneralSettings(
        id=1,
        darkmode=darkmode if darkmode is not None else get_default_darkmode(),
        language=language if language is not None else get_default_language(),
        auto_open_on_single_match=(
            auto_open_on_single_match
            if auto_open_on_single_match is not None
            else get_default_auto_open_on_single_match()
        ),
        start_screen=start_screen if start_screen is not None else get_default_start_screen(),
        always_tiles=always_tiles if always_tiles is not None else get_default_always_tiles(),
    )
    try:
        async with db.begin_nested():
            db.add(settings)
            await db.flush()
    except IntegrityError:
        return await get_first_general_settings(db)
    return settings


async def update_general_settings_darkmode(
    db: AsyncSession, settings: GeneralSettings, darkmode: bool
) -> GeneralSettings:
    """Update darkmode setting for existing record"""
    settings.darkmode = darkmode
    await db.flush()
    return settings


async def update_general_settings_language(
    db: AsyncSession, settings: GeneralSettings, language: str
) -> GeneralSettings:
    """Update language setting for existing record"""
    settings.language = language
    await db.flush()
    return settings


async def update_general_settings_all(
    db: AsyncSession,
    settings: GeneralSettings,
    darkmode: bool | None = None,
    language: str | None = None,
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
    always_tiles: bool | None = None,
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
