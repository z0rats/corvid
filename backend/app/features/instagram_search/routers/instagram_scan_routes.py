import asyncio
import logging

from fastapi import APIRouter, Request

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import SessionDep
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.features.instagram_search.crud.instagram_search_crud import INSTAGRAM_SCANS
from app.features.instagram_search.schemas.instagram_scan_schemas import (
    InstagramScanDetail,
    InstagramScanRequest,
    InstagramScanSummary,
)
from app.features.instagram_search.service.instagram_scan_service import (
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


add_run_routes(
    router,
    INSTAGRAM_SCANS,
    display_name="Instagram",
    noun="scan",
    summary_schema=InstagramScanSummary,
    detail_schema=InstagramScanDetail,
    not_found_code="INSTAGRAM_SCAN_NOT_FOUND",
)
