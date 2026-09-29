import asyncio
import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.scans.sse import sse_response
from app.features.steam_recon.crud.steam_recon_crud import (
    delete_search,
    get_search_with_result,
    list_searches,
)
from app.features.steam_recon.schemas.steam_recon_schemas import (
    ProfileRequest,
    ProfileResponse,
    ScanRequest,
    SearchDetail,
    SearchSummary,
)
from app.features.steam_recon.service.steam_profile_service import perform_profile_lookup
from app.features.steam_recon.service.steam_recon_scan_service import cancel_scan, run_scan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/steam-recon", tags=["Steam Recon"])


@router.post(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick lookup of a Steam profile",
    description="Resolves a SteamID64/3/2, profile URL or vanity name and returns the profile "
    "summary, ban record, Steam level, game count and external deep-links. Requires a Steam Web "
    "API key configured under Settings > API Keys.",
)
@limiter.limit("30/minute")
async def lookup_profile(
    request: Request, profile_request: ProfileRequest, db: ReadSessionDep
) -> ProfileResponse:
    logger.info("Steam profile lookup requested")
    result = await perform_profile_lookup(profile_request, db)
    logger.info("Steam profile lookup completed - steamid64: %s", result.profile.steamid64)
    return result


@router.post(
    "/scan",
    summary="Start a Steam Recon scan",
    description="Collects the target's friends graph, ranks close friends by mutual-connection "
    "weight, aggregates a geolocation hypothesis, and (if requested) scores the CS2 "
    "cheater-probability report. Streams progress as Server-Sent Events - a scan of a few "
    "hundred friends can take several minutes. Requires a Steam Web API key configured under "
    "Settings > API Keys.",
)
@limiter.limit("3/minute")
async def scan(request: Request, scan_request: ScanRequest):
    logger.info("Starting Steam Recon scan for target '%s'", scan_request.target)

    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(run_scan(scan_request, queue))

    return sse_response(queue)


@router.post(
    "/history/{search_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel a running scan",
    description="Cancel a currently-running Steam Recon scan",
    responses={404: {"description": "No running scan with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    if not await cancel_scan(search_id):
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running scan with that ID",
            error_code="STEAM_RECON_NOT_RUNNING",
        )
    logger.info("Cancellation requested for Steam Recon scan %s", search_id)


@router.get(
    "/history",
    response_model=list[SearchSummary],
    summary="List past Steam Recon scans",
    description="List past Steam Recon scans, most recent first",
)
async def read_searches(
    db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
) -> list[SearchSummary]:
    searches = await list_searches(db, skip=skip, limit=limit)
    return [SearchSummary.model_validate(s) for s in searches]


@router.get(
    "/history/{search_id}",
    response_model=SearchDetail,
    summary="Get a past Steam Recon scan",
    description="Get a past Steam Recon scan, including its full result",
    responses={404: {"description": "Scan not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> SearchDetail:
    search = await get_search_with_result(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
            error_code="STEAM_RECON_NOT_FOUND",
        )
    return SearchDetail.model_validate(search)


@router.delete(
    "/history/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Steam Recon scan",
    description="Permanently delete a past Steam Recon scan",
    responses={404: {"description": "Scan not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
            error_code="STEAM_RECON_NOT_FOUND",
        )
    logger.info("Deleted Steam Recon scan %s", search_id)
