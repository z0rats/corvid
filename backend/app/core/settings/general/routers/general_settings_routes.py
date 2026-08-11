"""General settings API routes"""

from app.core.dependencies import SessionDep
from app.core.settings.general.schemas.general_settings_schemas import (
    GeneralSettingsResponse,
    GeneralSettingsUpdate,
    DarkmodeUpdate,
    LanguageUpdate,
    CommandPaletteSettingsUpdate
)
from app.core.settings.general.service.general_settings_service import (
    get_general_settings,
    update_general_settings,
    update_darkmode_setting,
    update_language_setting,
    update_command_palette_settings
)
from app.core.settings.settings_router_factory import build_singleton_settings_router

router = build_singleton_settings_router(
    prefix="/api/settings/general",
    tags=["General Settings"],
    response_schema=GeneralSettingsResponse,
    update_schema=GeneralSettingsUpdate,
    get_service=get_general_settings,
    update_service=update_general_settings,
)


@router.put(
    "/darkmode",
    response_model=GeneralSettingsResponse,
    summary="Update darkmode setting",
    description="Update only the darkmode preference setting"
)
async def update_darkmode_endpoint(
    darkmode_update: DarkmodeUpdate,
    db: SessionDep
) -> GeneralSettingsResponse:
    return await update_darkmode_setting(db, darkmode_update)


@router.put(
    "/language",
    response_model=GeneralSettingsResponse,
    summary="Update language setting",
    description="Update only the UI language preference setting"
)
async def update_language_endpoint(
    language_update: LanguageUpdate,
    db: SessionDep
) -> GeneralSettingsResponse:
    return await update_language_setting(db, language_update)


@router.put(
    "/command-palette",
    response_model=GeneralSettingsResponse,
    summary="Update command palette settings",
    description="Update the command palette's own settings group (auto-open, start screen, always-tiles)"
)
async def update_command_palette_endpoint(
    command_palette_update: CommandPaletteSettingsUpdate,
    db: SessionDep
) -> GeneralSettingsResponse:
    return await update_command_palette_settings(db, command_palette_update)
