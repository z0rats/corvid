from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.singleton import get_or_create_singleton
from app.core.settings.username_search.models.social_analyzer_settings_models import (
    SocialAnalyzerConfig,
)
from app.core.settings.username_search.schemas.social_analyzer_settings_schemas import (
    SocialAnalyzerConfigUpdateSchema,
)


async def get_social_analyzer_config(db: AsyncSession) -> SocialAnalyzerConfig:
    """Retrieve social-analyzer configuration, creating defaults if not exists"""
    return await get_or_create_singleton(db, SocialAnalyzerConfig)


async def update_social_analyzer_config(
    db: AsyncSession, config_data: SocialAnalyzerConfigUpdateSchema
) -> SocialAnalyzerConfig:
    """Update social-analyzer configuration with only the provided fields"""
    config = await get_social_analyzer_config(db)
    for field, value in config_data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config
