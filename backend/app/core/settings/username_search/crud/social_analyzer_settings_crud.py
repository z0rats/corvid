import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.username_search.models.social_analyzer_settings_models import SocialAnalyzerConfig
from app.core.settings.username_search.schemas.social_analyzer_settings_schemas import SocialAnalyzerConfigUpdateSchema


async def get_social_analyzer_config(db: AsyncSession) -> SocialAnalyzerConfig:
    """Retrieve social-analyzer configuration, creating defaults if not exists"""
    result = await db.execute(select(SocialAnalyzerConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = SocialAnalyzerConfig()
        db.add(config)
        await db.flush()
        await db.refresh(config)
    return config


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


async def record_pypi_check(db: AsyncSession, latest_version: str | None) -> SocialAnalyzerConfig:
    """Record the result of a PyPI latest-version check"""
    config = await get_social_analyzer_config(db)
    config.latest_pypi_version = latest_version
    config.pypi_checked_at = datetime.datetime.now(datetime.timezone.utc)
    await db.flush()
    await db.refresh(config)
    return config
