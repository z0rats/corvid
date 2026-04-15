"""
API routes for keywords settings

Contains FastAPI route definitions for keyword management endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.settings.keywords.schemas.keywords_settings_schemas import (
    KeywordResponse,
    KeywordCreate,
    KeywordUpdate,
    KeywordListResponse,
    KeywordDeleteResponse,
)
from app.core.settings.keywords.service.keywords_settings_service import (
    get_all_keywords,
    get_keyword_by_id_service,
    create_keyword_service,
    update_keyword_service,
    delete_keyword_service
)
from app.core.settings.keywords.config.default_settings import (
    get_default_pagination_limit,
    validate_pagination_limit
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings/keywords", tags=["Keywords Settings"])


@router.get("", response_model=list[KeywordResponse], response_model_exclude_none=True)
async def get_keywords_endpoint(
    db: ReadSessionDep,
    skip: int = Query(0, ge=0, description="Number of keywords to skip"),
    limit: int = Query(None, ge=1, le=500, description="Maximum number of keywords to return"),
) -> list[KeywordResponse]:
    """
    Retrieve all keywords with pagination

    - **skip**: Number of keywords to skip (default: 0)
    - **limit**: Maximum number of keywords to return (default: 100, max: 500)
    """
    if limit is None:
        limit = get_default_pagination_limit()
    else:
        limit = validate_pagination_limit(limit)

    return await get_all_keywords(db, skip=skip, limit=limit)


@router.get(
    "/{keyword_id}",
    response_model=KeywordResponse,
    response_model_exclude_none=True,
    responses={404: {"description": "Keyword not found"}},
)
async def get_keyword_endpoint(
    keyword_id: int,
    db: ReadSessionDep
) -> KeywordResponse:
    """
    Retrieve a specific keyword by ID

    - **keyword_id**: The ID of the keyword to retrieve
    """
    return await get_keyword_by_id_service(db, keyword_id)


@router.post(
    "",
    response_model=KeywordResponse,
    response_model_exclude_none=True,
    status_code=201,
    responses={400: {"description": "Invalid keyword format or duplicate keyword"}},
)
async def create_keyword_endpoint(
    keyword_data: KeywordCreate,
    db: SessionDep
) -> KeywordResponse:
    """
    Create a new keyword

    - **keyword**: The keyword string to create (will be normalized)
    """
    return await create_keyword_service(db, keyword_data)


@router.put(
    "/{keyword_id}",
    response_model=KeywordResponse,
    response_model_exclude_none=True,
    responses={
        400: {"description": "Invalid keyword format or duplicate keyword"},
        404: {"description": "Keyword not found"},
    },
)
async def update_keyword_endpoint(
    keyword_id: int,
    keyword_data: KeywordUpdate,
    db: SessionDep
) -> KeywordResponse:
    """
    Update an existing keyword

    - **keyword_id**: The ID of the keyword to update
    - **keyword**: The new keyword string (will be normalized)
    """
    return await update_keyword_service(db, keyword_id, keyword_data)


@router.delete(
    "/{keyword_id}",
    response_model=KeywordDeleteResponse,
    responses={404: {"description": "Keyword not found"}},
)
async def delete_keyword_endpoint(
    keyword_id: int,
    db: SessionDep
) -> KeywordDeleteResponse:
    return await delete_keyword_service(db, keyword_id)
