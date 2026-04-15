"""API routes for trends blacklist management"""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.core.dependencies import ReadSessionDep, SessionDep
from app.features.newsfeed.crud.trends_blacklist_crud import (
    blacklist_entry_exists,
    create_blacklist_entry,
    delete_blacklist_entry,
    get_blacklist_entries,
)
from app.features.newsfeed.schemas.newsfeed_schemas import (
    BlacklistDeleteResponse,
    BlacklistEntryCreate,
    BlacklistEntryResponse,
    BlacklistType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings/newsfeed/trends-blacklist", tags=["Trends Blacklist"])


@router.get(
    "",
    response_model=list[BlacklistEntryResponse],
    summary="List blacklist entries",
    description="Retrieve all trends blacklist entries, optionally filtered by type",
)
async def list_blacklist_entries(
    db: ReadSessionDep,
    type: BlacklistType | None = Query(None, description="Filter by type: 'word' or 'ioc'"),
) -> list[BlacklistEntryResponse]:
    """List all blacklist entries, optionally filtered by type"""
    return await get_blacklist_entries(db, type)


@router.post(
    "",
    response_model=BlacklistEntryResponse,
    status_code=201,
    summary="Add blacklist entry",
    description="Add a word or IOC value to the trends blacklist",
)
async def add_blacklist_entry(
    entry_data: BlacklistEntryCreate,
    db: SessionDep,
) -> BlacklistEntryResponse:
    """Create a new blacklist entry"""
    if await blacklist_entry_exists(db, entry_data.value, entry_data.type):
        raise HTTPException(status_code=400, detail="Entry already exists in blacklist")

    entry = await create_blacklist_entry(db, entry_data.value, entry_data.type)
    logger.info("Added blacklist entry: type=%s, value=%s", entry_data.type, entry_data.value)
    return entry


@router.delete(
    "/{entry_id}",
    response_model=BlacklistDeleteResponse,
    summary="Remove blacklist entry",
    description="Remove an entry from the trends blacklist",
)
async def remove_blacklist_entry(
    entry_id: int,
    db: SessionDep,
) -> BlacklistDeleteResponse:
    """Delete a blacklist entry by ID"""
    deleted = await delete_blacklist_entry(db, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")

    logger.info("Removed blacklist entry: id=%s", entry_id)
    return BlacklistDeleteResponse(detail="Blacklist entry deleted successfully")
