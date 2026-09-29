import asyncio
import logging

from fastapi import APIRouter, Request

from app.core.config.rate_limit_config import limiter
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.features.phone_search.config.checkers_config import get_active_checkers
from app.features.phone_search.crud.phone_search_crud import PHONE_SEARCH_SCANS
from app.features.phone_search.schemas.phone_search_schemas import (
    PhoneSearchInfo,
    ScanRequest,
    SearchRunDetail,
    SearchRunSummary,
)
from app.features.phone_search.service.phone_search_service import run_scan

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


add_run_routes(
    router,
    PHONE_SEARCH_SCANS,
    display_name="phone",
    base="runs",
    summary_schema=SearchRunSummary,
    detail_schema=SearchRunDetail,
    not_found_code="PHONE_SEARCH_RUN_NOT_FOUND",
    not_running_code="PHONE_SEARCH_NOT_RUNNING",
    not_found_detail="Search run not found",
    with_results=True,
)
