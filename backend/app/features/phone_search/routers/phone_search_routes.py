import asyncio
import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.scans.sse import sse_response
from app.features.phone_search.config.checkers_config import get_active_checkers
from app.features.phone_search.crud.phone_search_crud import (
    delete_search_run,
    get_search_run_with_results,
    list_search_runs,
)
from app.features.phone_search.schemas.phone_search_schemas import (
    PhoneSearchInfo,
    ScanRequest,
    SearchRunDetail,
    SearchRunSummary,
)
from app.features.phone_search.service.phone_search_service import cancel_scan, run_scan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/phone-search", tags=["Phone Search"])


@router.post(
    "/scan",
    summary="Start a phone number search",
    description="Start a phone number registration search, streaming progress as Server-Sent "
    "Events. Checks a single phone number at a time - not built for bulk enumeration.",
)
@limiter.limit("3/minute")
async def start_scan(request: Request, scan_request: ScanRequest):
    """Start a new phone number search and stream its progress"""
    logger.info("Starting phone search")

    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(run_scan(scan_request.phone_number, queue))

    return sse_response(queue)


@router.post(
    "/runs/{search_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel a running search",
    description=(
        "Cancel a currently-running phone search, keeping whatever providers "
        "were found before cancellation"
    ),
    responses={404: {"description": "No running search with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    """Cancel a running scan"""
    if not await cancel_scan(search_id):
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running search with that ID",
            error_code="PHONE_SEARCH_NOT_RUNNING",
        )
    logger.info("Cancellation requested for phone search run %s", search_id)


@router.get(
    "/info",
    response_model=PhoneSearchInfo,
    summary="Get search tool info",
    description="Get the currently active provider checkers for phone search",
)
async def read_info() -> PhoneSearchInfo:
    """Get info about the currently active phone-search providers"""
    checkers = get_active_checkers()
    return PhoneSearchInfo(
        provider_count=len(checkers), providers=[c.PROVIDER_NAME for c in checkers]
    )


@router.get(
    "/runs",
    response_model=list[SearchRunSummary],
    summary="List past searches",
    description="Retrieve past and in-progress phone searches, most recent first",
)
async def read_search_runs(
    db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
) -> list[SearchRunSummary]:
    """List past search runs with pagination"""
    runs = await list_search_runs(db, skip=skip, limit=limit)
    return [SearchRunSummary.model_validate(r) for r in runs]


@router.get(
    "/runs/{search_id}",
    response_model=SearchRunDetail,
    summary="Get search run detail",
    description="Retrieve a specific search run including its found-provider results",
    responses={404: {"description": "Search run not found"}},
)
async def read_search_run(search_id: int, db: ReadSessionDep) -> SearchRunDetail:
    """Get a specific search run with its found providers"""
    run = await get_search_run_with_results(db, search_id)
    if not run:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search run not found",
            error_code="PHONE_SEARCH_RUN_NOT_FOUND",
        )
    return SearchRunDetail.model_validate(run)


@router.delete(
    "/runs/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete search run",
    description="Permanently delete a search run and its found-provider results",
    responses={404: {"description": "Search run not found"}},
)
async def delete_search_run_endpoint(search_id: int, db: SessionDep) -> None:
    """Delete a specific search run"""
    run = await delete_search_run(db, search_id)
    if not run:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search run not found",
            error_code="PHONE_SEARCH_RUN_NOT_FOUND",
        )
    logger.info("Deleted phone search run %s", search_id)
