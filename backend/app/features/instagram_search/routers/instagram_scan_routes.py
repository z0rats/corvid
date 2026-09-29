import asyncio
import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.scans.sse import sse_response
from app.features.instagram_search.crud.instagram_search_crud import (
    delete_search,
    get_search,
    list_searches,
)
from app.features.instagram_search.schemas.instagram_scan_schemas import (
    InstagramScanDetail,
    InstagramScanRequest,
    InstagramScanSummary,
)
from app.features.instagram_search.service.instagram_scan_service import (
    cancel_scan,
    run_scan_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/instagram-search", tags=["Instagram Search"])


@router.post(
    "/scan",
    summary="Scan an Instagram profile's followers, followees, or posts",
    description="Streams progress as Server-Sent Events. 'followers'/'followees' need an "
    "authorized session configured under Settings > API Keys - Instagram requires being "
    "logged in to see either list, regardless of the target profile's own privacy setting. "
    "Capped on item count and wall-clock time; a scan that hits either limit reports "
    "truncated: true with whatever it collected.",
)
@limiter.limit("3/minute")  # stricter than git_recon/amass's 5/minute - Instagram bans
# anonymous/session scraping more aggressively than a git clone or DNS enumeration.
async def scan(request: Request, db: SessionDep, scan_request: InstagramScanRequest):
    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(
        run_scan_task(
            username=scan_request.username,
            scan_type=scan_request.scan_type,
            db=db,
            queue=queue,
        )
    )
    return sse_response(queue)


@router.post(
    "/history/{search_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel a running scan",
    description="Cancel a currently-running Instagram scan, keeping whatever items were "
    "collected before cancellation",
    responses={404: {"description": "No running scan with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    if not await cancel_scan(search_id):
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running scan with that ID",
            error_code="INSTAGRAM_SCAN_NOT_FOUND",
        )
    logger.info("Cancellation requested for Instagram scan %s", search_id)


@router.get(
    "/history",
    response_model=list[InstagramScanSummary],
    summary="List past Instagram scans",
    description="List past followers/followees/posts scans, most recent first",
)
async def read_searches(
    db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
) -> list[InstagramScanSummary]:
    searches = await list_searches(db, skip=skip, limit=limit)
    return [InstagramScanSummary.model_validate(s) for s in searches]


@router.get(
    "/history/{search_id}",
    response_model=InstagramScanDetail,
    summary="Get a past Instagram scan",
    description="Get a past followers/followees/posts scan, including its full item list",
    responses={404: {"description": "Scan not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> InstagramScanDetail:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
            error_code="INSTAGRAM_SCAN_NOT_FOUND",
        )
    return InstagramScanDetail.model_validate(search)


@router.delete(
    "/history/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an Instagram scan",
    description="Permanently delete a past Instagram scan",
    responses={404: {"description": "Scan not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
            error_code="INSTAGRAM_SCAN_NOT_FOUND",
        )
    logger.info("Deleted Instagram scan %s", search_id)
