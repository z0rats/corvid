"""General settings business logic service"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.settings.general.schemas.general_settings_schemas import (
    GeneralSettingsResponse,
    GeneralSettingsUpdate,
    DarkmodeUpdate,
    FontUpdate
)
from app.core.settings.general.crud.general_settings_crud import (
    get_first_general_settings,
    create_general_settings,
    update_general_settings_all,
    update_general_settings_darkmode,
    update_general_settings_font
)
from app.core.settings.general.utils.validation_utils import (
    validate_font_name,
    normalize_font_name
)
from app.core.settings.general.config.default_settings import (
    get_default_darkmode,
    get_default_font
)

logger = logging.getLogger(__name__)


async def get_general_settings(db: AsyncSession) -> GeneralSettingsResponse:
    """Retrieve current general settings, creating defaults if none exist"""
    settings = await get_first_general_settings(db)

    if not settings:
        logger.info("No general settings found, creating default settings")
        settings = create_general_settings(db)
        await db.flush()
        await db.refresh(settings)

    return GeneralSettingsResponse.model_validate(settings)


async def update_general_settings(
    db: AsyncSession,
    settings_update: GeneralSettingsUpdate
) -> GeneralSettingsResponse:
    """Update general settings with provided values"""
    normalized_font = None
    if settings_update.font is not None:
        if not validate_font_name(settings_update.font):
            raise ApplicationError("Invalid font name format", status_code=400)
        normalized_font = normalize_font_name(settings_update.font)

    settings = await get_first_general_settings(db)

    if not settings:
        settings = create_general_settings(
            db,
            darkmode=settings_update.darkmode or get_default_darkmode(),
            font=normalized_font or get_default_font()
        )
    else:
        settings = update_general_settings_all(
            db,
            settings,
            darkmode=settings_update.darkmode,
            font=normalized_font
        )

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated general settings: darkmode=%s, font=%s", settings.darkmode, settings.font)
    return GeneralSettingsResponse.model_validate(settings)


async def update_darkmode_setting(
    db: AsyncSession,
    darkmode_update: DarkmodeUpdate
) -> GeneralSettingsResponse:
    """Update only the darkmode setting"""
    settings = await get_first_general_settings(db)

    if not settings:
        settings = create_general_settings(db, darkmode=darkmode_update.darkmode)
    else:
        settings = update_general_settings_darkmode(db, settings, darkmode_update.darkmode)

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated darkmode setting to: %s", darkmode_update.darkmode)
    return GeneralSettingsResponse.model_validate(settings)


async def update_font_setting(
    db: AsyncSession,
    font_update: FontUpdate
) -> GeneralSettingsResponse:
    """Update only the font setting"""
    if not validate_font_name(font_update.font):
        raise ApplicationError("Invalid font name format", status_code=400)

    normalized_font = normalize_font_name(font_update.font)
    settings = await get_first_general_settings(db)

    if not settings:
        settings = create_general_settings(db, font=normalized_font)
    else:
        settings = update_general_settings_font(db, settings, normalized_font)

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated font setting to: %s", normalized_font)
    return GeneralSettingsResponse.model_validate(settings)
