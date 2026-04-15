from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.ai_settings.models.ai_settings_models import AISettings
from app.core.settings.ai_settings.config.default_settings import DEFAULT_MODEL


async def get_ai_settings(db: AsyncSession) -> AISettings | None:
    """Retrieve the AI settings record"""
    stmt = select(AISettings).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_ai_settings(db: AsyncSession) -> AISettings:
    """Create default AI settings record"""
    settings = AISettings(default_model=DEFAULT_MODEL)
    db.add(settings)
    await db.flush()
    return settings


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
