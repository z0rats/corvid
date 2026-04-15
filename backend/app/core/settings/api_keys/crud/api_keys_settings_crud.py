import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.models.api_keys_settings_models import Apikey
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import ApikeyCreateRequest

logger = logging.getLogger(__name__)


async def create_new_apikey(db: AsyncSession, apikey: ApikeyCreateRequest) -> Apikey:
    """Create a new API key in the database"""
    try:
        db_apikey = Apikey(**apikey.model_dump())
        db.add(db_apikey)
        await db.flush()
        logger.debug("Created API key in database: %s", apikey.name)
        return db_apikey
    except SQLAlchemyError as e:
        logger.error("Database error creating API key %s: %s", apikey.name, e)
        raise


async def get_apikeys(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Apikey]:
    """Retrieve all API keys from the database"""
    try:
        result = await db.execute(select(Apikey).offset(skip).limit(limit))
        return list(result.scalars().all())
    except SQLAlchemyError as e:
        logger.error("Database error retrieving API keys: %s", e)
        raise


async def get_apikey(db: AsyncSession, name: str) -> Apikey | None:
    """Retrieve a single API key by name, returns None if not found"""
    try:
        result = await db.execute(select(Apikey).where(Apikey.name == name))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("Database error retrieving API key %s: %s", name, e)
        raise


async def upsert_apikey_bulk_lookup(db: AsyncSession, name: str, bulk_ioc_lookup: bool) -> Apikey:
    """Update bulk_ioc_lookup for an existing key, or create a minimal record if none exists."""
    try:
        db_apikey = await get_apikey(db, name)
        if db_apikey:
            db_apikey.bulk_ioc_lookup = bulk_ioc_lookup
        else:
            db_apikey = Apikey(name=name, key="", is_active=False, bulk_ioc_lookup=bulk_ioc_lookup)
            db.add(db_apikey)
        await db.flush()
        await db.refresh(db_apikey)
        logger.debug("Upserted bulk lookup setting for API key: %s", name)
        return db_apikey
    except SQLAlchemyError as e:
        logger.error("Database error upserting bulk lookup for %s: %s", name, e)
        raise


async def delete_existing_apikey(db: AsyncSession, name: str) -> bool:
    """Delete an API key by name. Returns True if deleted, False if not found."""
    try:
        db_apikey = await get_apikey(db, name)
        if not db_apikey:
            return False
        await db.delete(db_apikey)
        await db.flush()
        logger.debug("Deleted API key from database: %s", name)
        return True
    except SQLAlchemyError as e:
        logger.error("Database error deleting API key %s: %s", name, e)
        raise
