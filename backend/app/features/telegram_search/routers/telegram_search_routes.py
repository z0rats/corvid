import asyncio
import logging

from fastapi import APIRouter, Request

from app.core.config.rate_limit_config import limiter
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.features.telegram_search.crud.telegram_search_crud import TELEGRAM_SEARCH_SCANS
from app.features.telegram_search.schemas.telegram_search_schemas import (
    ScanRequest,
    SearchDetail,
    SearchSummary,
)
from app.features.telegram_search.service.telegram_scan_service import run_scan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telegram-search", tags=["Telegram Search"])


@router.post(
    "/scan",
    summary="Start a Telegram channel analytics scan",
    description="Reads a public channel's or group's t.me card (title, description, subscriber "
    "or member count), samples its newest posts from the t.me/s web preview, and computes "
    "activity metrics (views, posting rate, forwarded share, top forward sources, mentions) plus "
    "indicators from the sampled posts. Keyless, no Telegram account. Streams progress as "
    "Server-Sent Events.",
)
@limiter.limit("10/minute")
async def scan(request: Request, scan_request: ScanRequest):
    logger.info("Starting Telegram channel scan for @%s", scan_request.channel)

    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(run_scan(scan_request, queue))

    return sse_response(queue)


add_run_routes(
    router,
    TELEGRAM_SEARCH_SCANS,
    display_name="Telegram channel",
    noun="scan",
    summary_schema=SearchSummary,
    detail_schema=SearchDetail,
    not_found_code="TELEGRAM_SEARCH_NOT_FOUND",
    not_running_code="TELEGRAM_SEARCH_NOT_RUNNING",
    with_results=True,
)
