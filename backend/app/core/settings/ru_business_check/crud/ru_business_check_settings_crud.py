from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.ru_business_check.models.ru_business_check_settings_models import (
    RuBusinessCheckSettings,
)
from app.core.settings.ru_business_check.schemas.ru_business_check_settings_schemas import (
    RuBusinessCheckSettingsUpdateSchema,
)
from app.core.settings.singleton import get_or_create_singleton


async def get_ru_business_check_settings(db: AsyncSession) -> RuBusinessCheckSettings:
    """Retrieve RU Business Check settings, creating defaults if not exists"""
    return await get_or_create_singleton(db, RuBusinessCheckSettings)


async def update_ru_business_check_settings(
    db: AsyncSession, settings_data: RuBusinessCheckSettingsUpdateSchema
) -> RuBusinessCheckSettings:
    """Update RU Business Check settings with only the provided fields"""
    config = await get_ru_business_check_settings(db)
    for field, value in settings_data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config
