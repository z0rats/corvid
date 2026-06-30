"""General settings API routes"""

from fastapi import APIRouter

from app.core.dependencies import SessionDep
from app.core.settings.general.schemas.general_settings_schemas import (
    GeneralSettingsResponse,
    GeneralSettingsUpdate,
    DarkmodeUpdate,
    FontUpdate,
    LanguageUpdate
)
from app.core.settings.general.service.general_settings_service import (
    get_general_settings,
    update_general_settings,
    update_darkmode_setting,
    update_font_setting,
    update_language_setting
)

router = APIRouter(prefix="/api/settings/general", tags=["General Settings"])


@router.get(
    "",
    response_model=GeneralSettingsResponse,
    summary="Get general settings",
    description="Retrieve current general application settings including darkmode and font preferences"
)
async def get_general_settings_endpoint(db: SessionDep) -> GeneralSettingsResponse:
    return await get_general_settings(db)


@router.put(
    "",
    response_model=GeneralSettingsResponse,
    summary="Update general settings",
    description="Update general application settings with provided values"
)
async def update_general_settings_endpoint(
    settings_update: GeneralSettingsUpdate,
    db: SessionDep
) -> GeneralSettingsResponse:
    return await update_general_settings(db, settings_update)


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
    "/font",
    response_model=GeneralSettingsResponse,
    summary="Update font setting",
    description="Update only the font family preference setting"
)
async def update_font_endpoint(
    font_update: FontUpdate,
    db: SessionDep
) -> GeneralSettingsResponse:
    return await update_font_setting(db, font_update)


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
