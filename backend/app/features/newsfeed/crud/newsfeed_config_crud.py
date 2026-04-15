import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.models.newsfeed_models import NewsfeedConfig
from app.features.newsfeed.schemas.newsfeed_schemas import NewsfeedConfigSchema, NewsfeedConfigUpdateSchema

logger = logging.getLogger(__name__)


async def get_newsfeed_config(db: AsyncSession) -> NewsfeedConfig:
    """Retrieve newsfeed configuration, create default if not exists"""
    result = await db.execute(select(NewsfeedConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = NewsfeedConfig()
        db.add(config)
        await db.flush()
        await db.refresh(config)
    return config


async def update_newsfeed_config(db: AsyncSession, config_data: NewsfeedConfigUpdateSchema) -> NewsfeedConfig:
    """Update newsfeed configuration with only the provided fields"""
    config = await get_newsfeed_config(db)
    for field, value in config_data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config


async def get_retention_days(db: AsyncSession) -> int | None:
    """Get current retention days setting"""
    config = await get_newsfeed_config(db)
    return config.retention_days if config else None


async def set_retention_days(db: AsyncSession, new_retention_days: int) -> NewsfeedConfig:
    """Update retention days setting"""
    return await update_newsfeed_config(
        db, NewsfeedConfigUpdateSchema(retention_days=new_retention_days)
    )


async def update_last_fetch_timestamp(db: AsyncSession) -> None:
    """Update the last fetch timestamp to current time"""
    config = await get_newsfeed_config(db)
    config.last_fetch_timestamp = datetime.now(timezone.utc)
    await db.flush()


async def is_background_fetch_enabled(db: AsyncSession) -> bool:
    """Check if background fetch is enabled"""
    config = await get_newsfeed_config(db)
    return config.background_fetch_enabled if config else False


async def is_keyword_matching_enabled(db: AsyncSession) -> bool:
    """Check if keyword matching is enabled"""
    config = await get_newsfeed_config(db)
    return config.keyword_matching_enabled if config else False


async def get_fetch_interval_minutes(db: AsyncSession) -> int:
    """Get fetch interval in minutes"""
    config = await get_newsfeed_config(db)
    return config.fetch_interval_minutes if config else 60
