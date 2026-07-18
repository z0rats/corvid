import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.username_search.models.username_search_settings_models import UsernameSearchConfig
from app.core.settings.username_search.schemas.username_search_settings_schemas import UsernameSearchConfigUpdateSchema


async def get_username_search_config(db: AsyncSession) -> UsernameSearchConfig:
    """Retrieve username search configuration, creating defaults if not exists"""
    result = await db.execute(select(UsernameSearchConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = UsernameSearchConfig()
        db.add(config)
        await db.flush()
        await db.refresh(config)
    return config


async def update_username_search_config(
    db: AsyncSession, config_data: UsernameSearchConfigUpdateSchema
) -> UsernameSearchConfig:
    """Update username search configuration with only the provided fields"""
    config = await get_username_search_config(db)
    for field, value in config_data.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    await db.flush()
    await db.refresh(config)
    return config


async def record_db_refresh(db: AsyncSession, site_count: int) -> UsernameSearchConfig:
    """Record the result of a site-database refresh check.

    Separate from `update_username_search_config` since these are
    system-managed status fields, not user-settable ones.
    """
    config = await get_username_search_config(db)
    config.db_site_count = site_count
    config.db_last_updated_at = datetime.datetime.now(datetime.timezone.utc)
    await db.flush()
    await db.refresh(config)
    return config


async def record_pypi_check(db: AsyncSession, latest_version: str | None) -> UsernameSearchConfig:
    """Record the result of a PyPI latest-version check for the maigret package"""
    config = await get_username_search_config(db)
    config.latest_pypi_version = latest_version
    config.pypi_checked_at = datetime.datetime.now(datetime.timezone.utc)
    await db.flush()
    await db.refresh(config)
    return config
