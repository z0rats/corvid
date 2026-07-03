import logging

from fastapi import APIRouter, status

from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.ioc_lookup.single_lookup.crud.lookup_history_crud import (
    create_search,
    delete_search,
    get_search_with_results,
    list_searches,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.schemas.lookup_history_schemas import (
    SearchCreate,
    SearchDetail,
    SearchSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ioc-lookup/history", tags=["IOC Lookup"])


@router.post(
    "",
    response_model=SearchDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Save a completed single-IOC lookup search",
    description="Persist a single-IOC lookup search and its per-service results to history",
)
async def save_search(db: SessionDep, search_request: SearchCreate) -> SearchDetail:
    search = await create_search(db, search_request.ioc, search_request.ioc_type, search_request.results)
    logger.info("Saved single lookup search %s for '%s'", search.id, search_request.ioc)
    return await get_search_with_results(db, search.id)


@router.get(
    "",
    response_model=list[SearchSummary],
    summary="List past single-IOC lookup searches",
    description="List past single-IOC lookup searches, most recent first",
)
async def read_searches(db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100) -> list[SearchSummary]:
    return await list_searches(db, skip, limit)


@router.get(
    "/{search_id}",
    response_model=SearchDetail,
    summary="Get a single-IOC lookup search",
    description="Get a past single-IOC lookup search, including its per-service results",
    responses={404: {"description": "Search not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> SearchDetail:
    search = await get_search_with_results(db, search_id)
    if not search:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="LOOKUP_HISTORY_NOT_FOUND")
    return search


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a single-IOC lookup search",
    description="Delete a past single-IOC lookup search from history",
    responses={404: {"description": "Search not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="LOOKUP_HISTORY_NOT_FOUND")
    logger.info("Deleted single lookup search %s", search_id)
