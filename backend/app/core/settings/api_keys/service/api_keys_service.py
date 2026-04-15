import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.schemas.api_keys_settings_schemas import (
    ApikeySchema,
    ApikeyCreateRequest,
    ApikeyUpdateRequest,
    DeleteApikeyResponse,
)
from app.core.settings.api_keys.crud.api_keys_settings_crud import (
    create_new_apikey,
    get_apikeys,
    get_apikey,
    delete_existing_apikey,
    upsert_apikey_bulk_lookup,
)
from app.utils.llm_service import invalidate_model_registry_cache

logger = logging.getLogger(__name__)


async def create_apikey_service(db: AsyncSession, apikey_data: ApikeyCreateRequest) -> ApikeySchema | None:
    """Create a new API key entry. Returns None if key already exists."""
    if await get_apikey(db, apikey_data.name) is not None:
        return None

    db_apikey = await create_new_apikey(db, apikey_data)
    db_apikey.is_active = True
    await db.flush()
    await db.refresh(db_apikey)
    logger.info("Created API key: %s", apikey_data.name)
    return ApikeySchema.model_validate(db_apikey)


async def delete_apikey_service(db: AsyncSession, name: str) -> DeleteApikeyResponse | None:
    """Delete an API key by name. Clears the key value and disables the entry."""
    apikey = await get_apikey(db, name)
    if not apikey:
        return None

    apikey.key = ""
    apikey.is_active = False
    await db.flush()
    await db.refresh(apikey)
    logger.info("Deleted API key: %s", name)
    return DeleteApikeyResponse(apikey=ApikeySchema.model_validate(apikey), message="API key deleted successfully")


async def get_all_apikeys_active_status(db: AsyncSession) -> dict[str, bool]:
    """Get active status for all API keys"""
    return {apikey.name: apikey.is_active for apikey in await get_apikeys(db)}


async def get_apikey_active_status(db: AsyncSession, name: str) -> bool | None:
    """Get active status for a specific API key. Returns None if not found."""
    apikey = await get_apikey(db, name)
    if not apikey:
        return None
    return apikey.is_active


async def update_apikey_active_status(db: AsyncSession, name: str, is_active: bool) -> ApikeySchema | None:
    """Update active status for a specific API key. Returns None if not found."""
    db_apikey = await get_apikey(db, name)
    if not db_apikey:
        return None

    db_apikey.is_active = is_active
    await db.flush()
    await db.refresh(db_apikey)
    logger.info("Updated API key active status: %s -> %s", name, is_active)
    return ApikeySchema.model_validate(db_apikey)


async def get_all_apikeys_bulk_lookup_status(db: AsyncSession) -> dict[str, bool]:
    """Get bulk lookup status for all API keys"""
    return {apikey.name: apikey.bulk_ioc_lookup for apikey in await get_apikeys(db)}


async def get_apikey_bulk_lookup_status(db: AsyncSession, name: str) -> bool | None:
    """Get bulk lookup status for a specific API key. Returns None if not found."""
    apikey = await get_apikey(db, name)
    if not apikey:
        return None
    return apikey.bulk_ioc_lookup


async def update_apikey_bulk_lookup_status(db: AsyncSession, name: str, bulk_ioc_lookup: bool) -> ApikeySchema | None:
    """Update bulk lookup status for a specific API key. Returns None if not found."""
    db_apikey = await get_apikey(db, name)
    if not db_apikey:
        return None

    db_apikey.bulk_ioc_lookup = bulk_ioc_lookup
    await db.flush()
    await db.refresh(db_apikey)
    logger.info("Updated API key bulk lookup status: %s -> %s", name, bulk_ioc_lookup)
    return ApikeySchema.model_validate(db_apikey)


async def upsert_apikey_bulk_lookup_status(db: AsyncSession, name: str, bulk_ioc_lookup: bool) -> ApikeySchema:
    """Upsert bulk lookup status: update if exists, create minimal record if not."""
    db_apikey = await upsert_apikey_bulk_lookup(db, name, bulk_ioc_lookup)
    await db.refresh(db_apikey)
    logger.info("Upserted API key bulk lookup status: %s -> %s", name, bulk_ioc_lookup)
    return ApikeySchema.model_validate(db_apikey)


async def update_apikey_service(db: AsyncSession, name: str, apikey_data: ApikeyUpdateRequest) -> ApikeySchema | None:
    """Update an existing API key with the provided fields. Returns None if not found."""
    db_apikey = await get_apikey(db, name)
    if not db_apikey:
        return None

    if apikey_data.key is not None:
        db_apikey.key = apikey_data.key
    if apikey_data.is_active is not None:
        db_apikey.is_active = apikey_data.is_active
    if apikey_data.bulk_ioc_lookup is not None:
        db_apikey.bulk_ioc_lookup = apikey_data.bulk_ioc_lookup

    await db.flush()
    await db.refresh(db_apikey)
    invalidate_model_registry_cache()
    logger.info("Updated API key: %s", name)
    return ApikeySchema.model_validate(db_apikey)


async def get_all_apikeys_configured_status(db: AsyncSession) -> dict[str, bool]:
    """Get configuration status (has key value) for all API keys"""
    return {apikey.name: bool(apikey.key and apikey.key.strip()) for apikey in await get_apikeys(db)}
