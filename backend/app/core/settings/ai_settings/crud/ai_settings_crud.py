from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.ai_settings.models.ai_settings_models import AISettings
from app.core.settings.ai_settings.config.default_settings import DEFAULT_MODEL
from app.core.settings.singleton import get_or_create_singleton


async def get_ai_settings(db: AsyncSession) -> AISettings:
    """Retrieve the AI settings record, creating defaults if not exists"""
    return await get_or_create_singleton(db, AISettings, {"default_model": DEFAULT_MODEL})


async def update_ai_settings(
    db: AsyncSession,
    settings: AISettings,
    **fields: str | None,
) -> AISettings:
    """Update AI settings fields"""
    for key, value in fields.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    await db.flush()
    return settings
