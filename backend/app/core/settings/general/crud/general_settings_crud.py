"""General settings database operations"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.settings.general.models.general_settings_models import GeneralSettings
from app.core.settings.general.config.default_settings import (
    get_default_darkmode,
    get_default_font
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
    font: str | None = None
) -> GeneralSettings:
    """Create new general settings record"""
    settings = GeneralSettings(
        darkmode=darkmode if darkmode is not None else get_default_darkmode(),
        font=font if font is not None else get_default_font()
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


async def update_general_settings_font(
    db: AsyncSession,
    settings: GeneralSettings,
    font: str
) -> GeneralSettings:
    """Update font setting for existing record"""
    settings.font = font
    await db.flush()
    return settings


async def update_general_settings_all(
    db: AsyncSession,
    settings: GeneralSettings,
    darkmode: bool | None = None,
    font: str | None = None
) -> GeneralSettings:
    """Update multiple settings fields for existing record"""
    if darkmode is not None:
        settings.darkmode = darkmode
    if font is not None:
        settings.font = font
    await db.flush()
    return settings


async def delete_general_settings(db: AsyncSession, settings: GeneralSettings) -> None:
    """Delete general settings record"""
    await db.delete(settings)
    await db.flush()
