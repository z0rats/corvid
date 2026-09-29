import asyncio
import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.scans.sse import sse_response
from app.features.amass.crud.amass_crud import delete_search, get_search, list_searches
from app.features.amass.schemas.amass_schemas import ScanRequest, SearchDetail, SearchSummary
from app.features.amass.service.amass_service import cancel_scan, get_amass_version, run_scan_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/amass", tags=["Amass"])


@router.post(
    "/scan",
    summary="Run an active amass enumeration scan for a domain",
    description=(
        "Actively enumerate a domain's hosts via amass's passive sources plus (optionally) "
        "wordlist brute-forcing. Streams progress as Server-Sent Events - a scan can run for "
        "several minutes, too long to hold open as a single request behind most reverse "
        "proxies. Findings accumulate in amass's own engine across every scan of the same "
        "domain, so a repeat scan reflects everything known so far, not just this run."
    ),
)
@limiter.limit("5/minute")
async def scan(request: Request, db: SessionDep, scan_request: ScanRequest):
    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(
        run_scan_task(domain=scan_request.domain, brute_force=scan_request.brute_force, queue=queue)
    )
    return sse_response(queue)


@router.post(
    "/history/{search_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel a running scan",
    description="Cancel a currently-running amass scan, keeping whatever hosts were "
    "discovered before cancellation",
    responses={404: {"description": "No running search with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    if not await cancel_scan(search_id):
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running search with that ID",
            error_code="AMASS_NOT_FOUND",
        )
    logger.info("Cancellation requested for amass search %s", search_id)


@router.get(
    "/history",
    response_model=list[SearchSummary],
    summary="List past amass scans",
    description="List past amass scans, most recent first",
)
async def read_searches(
    db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
) -> list[SearchSummary]:
    searches = await list_searches(db, skip=skip, limit=limit)
    return [SearchSummary.model_validate(s) for s in searches]


@router.get(
    "/history/{search_id}",
    response_model=SearchDetail,
    summary="Get a past amass scan",
    description="Get a past amass scan, including its full result",
    responses={404: {"description": "Search not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> SearchDetail:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
            error_code="AMASS_NOT_FOUND",
        )
    return SearchDetail.model_validate(search)


@router.delete(
    "/history/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an amass scan",
    description="Permanently delete a past amass scan",
    responses={404: {"description": "Search not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
            error_code="AMASS_NOT_FOUND",
        )
    logger.info("Deleted amass search %s", search_id)


@router.get(
    "/health",
    summary="Check amass service health",
    description="Report whether the amass binary is installed and its version",
)
async def health() -> dict[str, str | bool | None]:
    version = get_amass_version()
    return {"service": "amass", "amass_installed": version is not None, "amass_version": version}
