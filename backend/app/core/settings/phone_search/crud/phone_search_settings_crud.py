from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.phone_search.models.phone_search_settings_models import PhoneSearchConfig
from app.core.settings.phone_search.schemas.phone_search_settings_schemas import (
    PhoneSearchConfigUpdateSchema,
)
from app.core.settings.singleton import get_or_create_singleton


async def get_phone_search_config(db: AsyncSession) -> PhoneSearchConfig:
    """Retrieve phone search configuration, creating defaults if not exists"""
    return await get_or_create_singleton(db, PhoneSearchConfig)


async def update_phone_search_config(
    db: AsyncSession, config_data: PhoneSearchConfigUpdateSchema
) -> PhoneSearchConfig:
    """Update phone search configuration with only the provided fields"""
    config = await get_phone_search_config(db)
    for field, value in config_data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config
