import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Query, Request

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.core.settings.email_search.crud.email_search_settings_crud import get_email_search_config
from app.core.utils.pypi_version_check import check_for_update, compute_update_available
from app.features.email_search.config.mailcat_config import (
    DEFAULT_CHECKERS,
    HEADLESS_CHECKERS,
    PACKAGE_NAME,
    SMTP_CHECKERS,
    get_installed_version,
)
from app.features.email_search.config.user_scanner_config import (
    PACKAGE_NAME as USER_SCANNER_PACKAGE_NAME,
)
from app.features.email_search.config.user_scanner_config import (
    get_installed_version as get_user_scanner_version,
)
from app.features.email_search.config.user_scanner_config import (
    is_available as user_scanner_available,
)
from app.features.email_search.config.user_scanner_config import runnable_module_count
from app.features.email_search.crud.email_search_crud import EMAIL_SEARCH_SCANS
from app.features.email_search.schemas.email_search_schemas import (
    EmailSearchInfo,
    ScanRequest,
    SearchRunDetail,
    SearchRunSummary,
)
from app.features.email_search.service.email_search_service import run_scan
from app.features.email_search.service.user_scanner_service import (
    PROXY_UNSUPPORTED_MESSAGE,
)
from app.features.email_search.service.user_scanner_service import (
    run_scan as run_user_scanner_scan,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email-search", tags=["Email Search"])


def _active_provider_count(config) -> int:
    count = len(DEFAULT_CHECKERS)
    if config.enable_smtp_checks:
        count += len(SMTP_CHECKERS)
    if config.enable_headless_checks:
        count += len(HEADLESS_CHECKERS)
    return count


@router.post(
    "/scan",
    summary="Start an email search",
    description="Start a mailcat email search, streaming progress as Server-Sent Events",
)
@limiter.limit("3/minute")
async def start_scan(request: Request, scan_request: ScanRequest):
    """Start a new email search and stream its progress"""
    logger.info("Starting %s email search for '%s'", scan_request.source, scan_request.username)

    queue: asyncio.Queue = asyncio.Queue()
    runner = run_user_scanner_scan if scan_request.source == "user_scanner" else run_scan
    asyncio.create_task(runner(scan_request.username, queue))

    return sse_response(queue)


@router.get(
    "/info",
    response_model=EmailSearchInfo,
    summary="Get search tool info",
    description=(
        "Get the underlying tool's installed version, active provider count, and (mailcat "
        "only) whether a newer version is available on PyPI"
    ),
)
async def read_info(
    db: ReadSessionDep, source: Literal["mailcat", "user_scanner"] = Query(default="mailcat")
) -> EmailSearchInfo:
    """Get info about an email search tool and its installed/available version"""
    if source == "user_scanner":
        available = user_scanner_available()
        config = await get_email_search_config(db)
        routed = bool(config.proxy_url or config.use_tor)
        return EmailSearchInfo(
            tool=USER_SCANNER_PACKAGE_NAME,
            version=get_user_scanner_version() if available else "",
            provider_count=runnable_module_count(),
            available=available,
            blocked_reason=PROXY_UNSUPPORTED_MESSAGE if routed else None,
        )
    config = await get_email_search_config(db)
    installed_version = get_installed_version()

    return EmailSearchInfo(
        tool="mailcat",
        version=installed_version,
        provider_count=_active_provider_count(config),
        latest_version=config.latest_pypi_version,
        update_available=compute_update_available(config.latest_pypi_version, installed_version),
    )


@router.post(
    "/check-update",
    response_model=EmailSearchInfo,
    summary="Check PyPI for a mailcat-osint update",
    description="Check PyPI for the latest published mailcat-osint version. Doesn't install "
    "anything - a newer version still requires a container rebuild, this only checks what's "
    "available.",
)
async def check_update(db: SessionDep) -> EmailSearchInfo:
    """Manually check PyPI for a newer mailcat-osint release"""
    config = await get_email_search_config(db)
    installed_version = get_installed_version()
    result = await check_for_update(db, PACKAGE_NAME, config, installed_version)

    return EmailSearchInfo(
        tool="mailcat",
        version=installed_version,
        provider_count=_active_provider_count(config),
        latest_version=result.latest_version,
        update_available=result.update_available,
    )


add_run_routes(
    router,
    EMAIL_SEARCH_SCANS,
    display_name="email",
    base="runs",
    summary_schema=SearchRunSummary,
    detail_schema=SearchRunDetail,
    not_found_code="EMAIL_SEARCH_RUN_NOT_FOUND",
    not_running_code="EMAIL_SEARCH_NOT_RUNNING",
    not_found_detail="Search run not found",
    with_results=True,
)
