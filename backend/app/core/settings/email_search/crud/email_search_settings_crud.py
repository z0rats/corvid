import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.email_search.models.email_search_settings_models import EmailSearchConfig
from app.core.settings.email_search.schemas.email_search_settings_schemas import EmailSearchConfigUpdateSchema


async def get_email_search_config(db: AsyncSession) -> EmailSearchConfig:
    """Retrieve email search configuration, creating defaults if not exists"""
    result = await db.execute(select(EmailSearchConfig))
    config = result.scalar_one_or_none()
    if not config:
        config = EmailSearchConfig()
        db.add(config)
        await db.flush()
        await db.refresh(config)
    return config


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


async def record_pypi_check(db: AsyncSession, latest_version: str | None) -> EmailSearchConfig:
    """Record the result of a PyPI latest-version check"""
    config = await get_email_search_config(db)
    config.latest_pypi_version = latest_version
    config.pypi_checked_at = datetime.datetime.now(datetime.timezone.utc)
    await db.flush()
    await db.refresh(config)
    return config
