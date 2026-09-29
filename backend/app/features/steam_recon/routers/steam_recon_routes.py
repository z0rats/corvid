import asyncio
import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.features.steam_recon.crud.steam_recon_crud import STEAM_RECON_SCANS
from app.features.steam_recon.schemas.steam_recon_schemas import (
    ProfileRequest,
    ProfileResponse,
    ScanRequest,
    SearchDetail,
    SearchSummary,
)
from app.features.steam_recon.service.steam_profile_service import perform_profile_lookup
from app.features.steam_recon.service.steam_recon_scan_service import run_scan

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


add_run_routes(
    router,
    STEAM_RECON_SCANS,
    display_name="Steam Recon",
    noun="scan",
    summary_schema=SearchSummary,
    detail_schema=SearchDetail,
    not_found_code="STEAM_RECON_NOT_FOUND",
    not_running_code="STEAM_RECON_NOT_RUNNING",
    with_results=True,
)
