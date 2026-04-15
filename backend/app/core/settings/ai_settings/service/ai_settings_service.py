import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.ai_settings.schemas.ai_settings_schemas import (
    AISettingsResponse,
    AISettingsUpdate,
)
from app.core.settings.ai_settings.crud.ai_settings_crud import (
    get_ai_settings,
    create_ai_settings,
    update_ai_settings,
)

logger = logging.getLogger(__name__)

MODULE_FIELDS = {
    "newsfeed_analysis_model",
    "newsfeed_report_model",
    "email_analyzer_model",
    "llm_templates_model",
}


async def get_or_create_ai_settings(db: AsyncSession) -> AISettingsResponse:
    """Retrieve current AI settings, creating defaults if none exist"""
    settings = await get_ai_settings(db)

    if not settings:
        logger.info("No AI settings found, creating defaults")
        settings = await create_ai_settings(db)
        await db.refresh(settings)

    return AISettingsResponse.model_validate(settings)


async def update_ai_settings_values(
    db: AsyncSession,
    settings_update: AISettingsUpdate,
) -> AISettingsResponse:
    """Update AI settings with provided values"""
    settings = await get_ai_settings(db)

    if not settings:
        settings = await create_ai_settings(db)

    fields: dict[str, str | None] = {}
    if settings_update.default_model is not None:
        fields["default_model"] = settings_update.default_model

    for field_name in MODULE_FIELDS:
        value = getattr(settings_update, field_name, None)
        if value is not None:
            fields[field_name] = value if value != "" else None

    if fields:
        settings = await update_ai_settings(db, settings, **fields)

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated AI settings: %s", fields)
    return AISettingsResponse.model_validate(settings)
