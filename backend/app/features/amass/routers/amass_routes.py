import asyncio
import logging

from fastapi import APIRouter, Request

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import SessionDep
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.features.amass.crud.amass_crud import AMASS_SCANS
from app.features.amass.schemas.amass_schemas import ScanRequest, SearchDetail, SearchSummary
from app.features.amass.service.amass_service import get_amass_version, run_scan_task

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


add_run_routes(
    router,
    AMASS_SCANS,
    display_name="amass",
    summary_schema=SearchSummary,
    detail_schema=SearchDetail,
    not_found_code="AMASS_NOT_FOUND",
)


@router.get(
    "/health",
    summary="Check amass service health",
    description="Report whether the amass binary is installed and its version",
)
async def health() -> dict[str, str | bool | None]:
    version = get_amass_version()
    return {"service": "amass", "amass_installed": version is not None, "amass_version": version}
