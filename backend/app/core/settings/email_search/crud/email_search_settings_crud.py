from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.email_search.models.email_search_settings_models import EmailSearchConfig
from app.core.settings.email_search.schemas.email_search_settings_schemas import (
    EmailSearchConfigUpdateSchema,
)
from app.core.settings.singleton import get_or_create_singleton


async def get_email_search_config(db: AsyncSession) -> EmailSearchConfig:
    """Retrieve email search configuration, creating defaults if not exists"""
    return await get_or_create_singleton(db, EmailSearchConfig)


async def update_email_search_config(
    db: AsyncSession, config_data: EmailSearchConfigUpdateSchema
) -> EmailSearchConfig:
    """Update email search configuration with only the provided fields"""
    config = await get_email_search_config(db)
    for field, value in config_data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config
