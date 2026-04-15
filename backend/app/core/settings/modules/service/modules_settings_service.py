"""Module settings business logic service"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.settings.modules.schemas.modules_settings_schemas import (
    ModuleSettingsResponse,
    ModuleSettingsCreate,
    ModuleSettingsUpdate,
    ModuleStatusUpdate
)
from app.core.settings.modules.crud.modules_settings_crud import (
    get_all_module_settings,
    get_module_setting_by_name,
    create_module_setting,
    update_module_setting_status,
    delete_module_setting,
    module_setting_exists
)
from app.core.settings.modules.utils.validation_utils import (
    validate_module_name,
    normalize_module_name,
    validate_enabled_status,
    is_supported_module
)
from app.core.settings.modules.config.default_settings import get_default_enabled_status

logger = logging.getLogger(__name__)


async def get_all_modules_settings(db: AsyncSession) -> list[ModuleSettingsResponse]:
    """Retrieve all module settings"""
    settings = await get_all_module_settings(db)
    return [ModuleSettingsResponse.model_validate(setting) for setting in settings]


async def get_module_setting(db: AsyncSession, module_name: str) -> ModuleSettingsResponse:
    """Retrieve specific module setting by name"""
    normalized_name = normalize_module_name(module_name)
    if not normalized_name:
        raise ApplicationError("Invalid module name format", status_code=400)

    setting = await get_module_setting_by_name(db, normalized_name)
    if not setting:
        raise ApplicationError("Module setting not found", status_code=404)

    return ModuleSettingsResponse.model_validate(setting)


async def create_new_module_setting(
    db: AsyncSession,
    module_data: ModuleSettingsCreate
) -> ModuleSettingsResponse:
    """Create new module setting"""
    normalized_name = normalize_module_name(module_data.name)
    if not normalized_name:
        raise ApplicationError("Invalid module name format", status_code=400)

    if not validate_enabled_status(module_data.enabled):
        raise ApplicationError("Invalid enabled status", status_code=400)

    if await module_setting_exists(db, normalized_name):
        raise ApplicationError("Module setting already exists", status_code=409)

    setting = create_module_setting(db, normalized_name, module_data.enabled)
    await db.flush()
    await db.refresh(setting)

    logger.info("Created module setting: %s", normalized_name)
    return ModuleSettingsResponse.model_validate(setting)


async def update_module_setting(
    db: AsyncSession,
    module_name: str,
    update_data: ModuleSettingsUpdate
) -> ModuleSettingsResponse:
    """Update existing module setting"""
    normalized_name = normalize_module_name(module_name)
    if not normalized_name:
        raise ApplicationError("Invalid module name format", status_code=400)

    setting = await get_module_setting_by_name(db, normalized_name)
    if not setting:
        raise ApplicationError("Module setting not found", status_code=404)

    if update_data.enabled is not None:
        if not validate_enabled_status(update_data.enabled):
            raise ApplicationError("Invalid enabled status", status_code=400)
        setting = update_module_setting_status(db, setting, update_data.enabled)

    await db.flush()
    await db.refresh(setting)

    logger.info("Updated module setting: %s", normalized_name)
    return ModuleSettingsResponse.model_validate(setting)


async def update_module_status(
    db: AsyncSession,
    module_name: str,
    status_data: ModuleStatusUpdate
) -> ModuleSettingsResponse:
    """Update only module enabled status"""
    normalized_name = normalize_module_name(module_name)
    if not normalized_name:
        raise ApplicationError("Invalid module name format", status_code=400)

    setting = await get_module_setting_by_name(db, normalized_name)
    if not setting:
        setting = create_module_setting(db, normalized_name, status_data.enabled)
    else:
        setting = update_module_setting_status(db, setting, status_data.enabled)

    await db.flush()
    await db.refresh(setting)

    status_text = "enabled" if status_data.enabled else "disabled"
    logger.info("Module %s %s", normalized_name, status_text)
    return ModuleSettingsResponse.model_validate(setting)


async def delete_module_setting_by_name(db: AsyncSession, module_name: str) -> None:
    """Delete module setting by name"""
    normalized_name = normalize_module_name(module_name)
    if not normalized_name:
        raise ApplicationError("Invalid module name format", status_code=400)

    setting = await get_module_setting_by_name(db, normalized_name)
    if not setting:
        raise ApplicationError("Module setting not found", status_code=404)

    delete_module_setting(db, setting)
    await db.flush()

    logger.info("Deleted module setting: %s", normalized_name)
