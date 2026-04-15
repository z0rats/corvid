"""Module settings CRUD operations"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.settings.modules.models.modules_settings_models import ModuleSettings
from app.core.settings.modules.config.default_settings import get_default_enabled_status


async def get_all_module_settings(db: AsyncSession) -> list[ModuleSettings]:
    """Retrieve all module settings from database"""
    stmt = select(ModuleSettings)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_module_setting_by_name(db: AsyncSession, module_name: str) -> ModuleSettings | None:
    """Retrieve specific module setting by name"""
    stmt = select(ModuleSettings).where(ModuleSettings.name == module_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def create_module_setting(db: AsyncSession, name: str, enabled: bool = None) -> ModuleSettings:
    """Create new module setting record"""
    if enabled is None:
        enabled = get_default_enabled_status()

    setting = ModuleSettings(name=name, enabled=enabled)
    db.add(setting)
    return setting


def update_module_setting_status(db: AsyncSession, setting: ModuleSettings, enabled: bool) -> ModuleSettings:
    """Update module setting enabled status"""
    setting.enabled = enabled
    return setting


async def delete_module_setting(db: AsyncSession, setting: ModuleSettings) -> None:
    """Delete module setting from database"""
    await db.delete(setting)


async def module_setting_exists(db: AsyncSession, module_name: str) -> bool:
    """Check if module setting exists in database"""
    stmt = select(ModuleSettings).where(ModuleSettings.name == module_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
