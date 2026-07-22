"""General settings business logic service"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.settings.general.schemas.general_settings_schemas import (
    GeneralSettingsResponse,
    GeneralSettingsUpdate,
    DarkmodeUpdate,
    LanguageUpdate,
    CommandPaletteSettingsUpdate
)
from app.core.settings.general.crud.general_settings_crud import (
    get_first_general_settings,
    create_general_settings,
    update_general_settings_all,
    update_general_settings_darkmode,
    update_general_settings_language,
    update_general_settings_command_palette
)
from app.core.settings.general.utils.validation_utils import (
    validate_language_code,
    validate_start_screen
)
from app.core.settings.general.config.default_settings import (
    get_default_darkmode,
    get_default_language
)

logger = logging.getLogger(__name__)


async def get_general_settings(db: AsyncSession) -> GeneralSettingsResponse:
    """Retrieve current general settings, creating defaults if none exist"""
    settings = await get_first_general_settings(db)

    if not settings:
        logger.info("No general settings found, creating default settings")
        settings = await create_general_settings(db)
        await db.flush()
        await db.refresh(settings)

    return GeneralSettingsResponse.model_validate(settings)


async def update_general_settings(
    db: AsyncSession,
    settings_update: GeneralSettingsUpdate
) -> GeneralSettingsResponse:
    """Update general settings with provided values"""
    normalized_language = None
    if settings_update.language is not None:
        if not validate_language_code(settings_update.language):
            raise ApplicationError("Unsupported language code", status_code=400)
        normalized_language = settings_update.language.strip().lower()

    settings = await get_first_general_settings(db)

    if not settings:
        settings = await create_general_settings(
            db,
            darkmode=settings_update.darkmode or get_default_darkmode(),
            language=normalized_language or get_default_language()
        )
    else:
        settings = await update_general_settings_all(
            db,
            settings,
            darkmode=settings_update.darkmode,
            language=normalized_language
        )

    await db.flush()
    await db.refresh(settings)

    logger.info(
        "Updated general settings: darkmode=%s, language=%s",
        settings.darkmode, settings.language
    )
    return GeneralSettingsResponse.model_validate(settings)


async def update_darkmode_setting(
    db: AsyncSession,
    darkmode_update: DarkmodeUpdate
) -> GeneralSettingsResponse:
    """Update only the darkmode setting"""
    settings = await get_first_general_settings(db)

    if not settings:
        settings = await create_general_settings(db, darkmode=darkmode_update.darkmode)
    else:
        settings = await update_general_settings_darkmode(db, settings, darkmode_update.darkmode)

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated darkmode setting to: %s", darkmode_update.darkmode)
    return GeneralSettingsResponse.model_validate(settings)


async def update_language_setting(
    db: AsyncSession,
    language_update: LanguageUpdate
) -> GeneralSettingsResponse:
    """Update only the language setting"""
    if not validate_language_code(language_update.language):
        raise ApplicationError("Unsupported language code", status_code=400)

    normalized_language = language_update.language.strip().lower()
    settings = await get_first_general_settings(db)

    if not settings:
        settings = await create_general_settings(db, language=normalized_language)
    else:
        settings = await update_general_settings_language(db, settings, normalized_language)

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated language setting to: %s", normalized_language)
    return GeneralSettingsResponse.model_validate(settings)


async def update_command_palette_settings(
    db: AsyncSession,
    command_palette_update: CommandPaletteSettingsUpdate
) -> GeneralSettingsResponse:
    """Update the command palette settings group"""
    normalized_start_screen = None
    if command_palette_update.start_screen is not None:
        if not validate_start_screen(command_palette_update.start_screen):
            raise ApplicationError("Unsupported start screen value", status_code=400)
        normalized_start_screen = command_palette_update.start_screen.strip().lower()

    settings = await get_first_general_settings(db)

    if not settings:
        settings = await create_general_settings(
            db,
            auto_open_on_single_match=command_palette_update.auto_open_on_single_match,
            start_screen=normalized_start_screen,
            always_tiles=command_palette_update.always_tiles
        )
    else:
        settings = await update_general_settings_command_palette(
            db,
            settings,
            auto_open_on_single_match=command_palette_update.auto_open_on_single_match,
            start_screen=normalized_start_screen,
            always_tiles=command_palette_update.always_tiles
        )

    await db.flush()
    await db.refresh(settings)

    logger.info(
        "Updated command palette settings: auto_open_on_single_match=%s, start_screen=%s, always_tiles=%s",
        settings.auto_open_on_single_match, settings.start_screen, settings.always_tiles
    )
    return GeneralSettingsResponse.model_validate(settings)
