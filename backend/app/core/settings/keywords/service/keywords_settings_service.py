"""Keywords settings business logic service"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.settings.keywords.schemas.keywords_settings_schemas import (
    KeywordResponse,
    KeywordCreate,
    KeywordUpdate
)
from app.core.settings.keywords.crud.keywords_settings_crud import (
    get_keywords_list,
    get_keyword_by_id,
    get_keyword_by_value,
    create_keyword_record,
    update_keyword_record,
    delete_keyword_record
)
from app.core.settings.keywords.utils.validation_utils import (
    validate_keyword_format,
    normalize_keyword
)

logger = logging.getLogger(__name__)


async def get_all_keywords(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[KeywordResponse]:
    """Retrieve all keywords with pagination"""
    keywords = await get_keywords_list(db, skip=skip, limit=limit)
    return [KeywordResponse.model_validate(keyword) for keyword in keywords]


async def get_keyword_by_id_service(db: AsyncSession, keyword_id: int) -> KeywordResponse:
    """Retrieve a specific keyword by ID"""
    keyword = await get_keyword_by_id(db, keyword_id)

    if not keyword:
        raise ApplicationError("Keyword not found", status_code=404)

    return KeywordResponse.model_validate(keyword)


async def create_keyword_service(db: AsyncSession, keyword_data: KeywordCreate) -> KeywordResponse:
    """Create a new keyword with validation"""
    if not validate_keyword_format(keyword_data.keyword):
        raise ApplicationError("Invalid keyword format", status_code=400)

    normalized_keyword = normalize_keyword(keyword_data.keyword)

    existing_keyword = await get_keyword_by_value(db, normalized_keyword)
    if existing_keyword:
        logger.warning("Attempt to create duplicate keyword: %s", normalized_keyword)
        raise ApplicationError("Keyword already exists", status_code=400)

    keyword = await create_keyword_record(db, normalized_keyword)
    await db.refresh(keyword)

    logger.info("Created new keyword: %s", normalized_keyword)
    return KeywordResponse.model_validate(keyword)


async def update_keyword_service(
    db: AsyncSession,
    keyword_id: int,
    keyword_data: KeywordUpdate
) -> KeywordResponse:
    """Update an existing keyword"""
    existing_keyword = await get_keyword_by_id(db, keyword_id)
    if not existing_keyword:
        raise ApplicationError("Keyword not found", status_code=404)

    if not validate_keyword_format(keyword_data.keyword):
        raise ApplicationError("Invalid keyword format", status_code=400)

    normalized_keyword = normalize_keyword(keyword_data.keyword)

    duplicate_keyword = await get_keyword_by_value(db, normalized_keyword)
    if duplicate_keyword and duplicate_keyword.id != keyword_id:
        raise ApplicationError("Keyword already exists", status_code=400)

    updated_keyword = await update_keyword_record(db, existing_keyword, normalized_keyword)
    await db.refresh(updated_keyword)

    logger.info("Updated keyword %s to: %s", keyword_id, normalized_keyword)
    return KeywordResponse.model_validate(updated_keyword)


async def delete_keyword_service(db: AsyncSession, keyword_id: int) -> dict:
    """Delete a keyword by ID"""
    keyword = await get_keyword_by_id(db, keyword_id)
    if not keyword:
        raise ApplicationError("Keyword not found", status_code=404)

    success = await delete_keyword_record(db, keyword_id)
    if not success:
        raise ApplicationError("Failed to delete keyword", status_code=500)

    await db.flush()
    logger.info("Deleted keyword with ID: %s", keyword_id)
    return {"detail": "Keyword deleted successfully"}
