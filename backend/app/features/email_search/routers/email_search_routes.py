import asyncio
import json
import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.settings.email_search.crud.email_search_settings_crud import (
    get_email_search_config,
    record_pypi_check,
)
from app.features.email_search.config.mailcat_config import (
    DEFAULT_CHECKERS,
    HEADLESS_CHECKERS,
    SMTP_CHECKERS,
    fetch_latest_pypi_version,
    get_installed_version,
)
from app.features.email_search.crud.email_search_crud import (
    delete_search_run,
    get_search_run_with_results,
    list_search_runs,
)
from app.features.email_search.schemas.email_search_schemas import (
    EmailSearchInfo,
    ScanRequest,
    SearchRunDetail,
    SearchRunSummary,
)
from app.features.email_search.service.email_search_service import cancel_scan, run_scan

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
    logger.info("Starting email search for '%s'", scan_request.username)

    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(run_scan(scan_request.username, queue))

    async def event_stream():
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/runs/{search_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Cancel a running search",
    description="Cancel a currently-running email search, keeping whatever providers were found before cancellation",
    responses={404: {"description": "No running search with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    """Cancel a running scan"""
    if not cancel_scan(search_id):
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No running search with that ID", error_code="EMAIL_SEARCH_NOT_RUNNING")
    logger.info("Cancellation requested for email search run %s", search_id)


@router.get(
    "/info",
    response_model=EmailSearchInfo,
    summary="Get search tool info",
    description="Get the underlying mailcat tool's installed version, active provider count, and whether a newer version is available on PyPI",
)
async def read_info(db: ReadSessionDep) -> EmailSearchInfo:
    """Get info about the mailcat tool and its installed/available version"""
    config = await get_email_search_config(db)
    installed_version = get_installed_version()
    update_available = (
        bool(config.latest_pypi_version) and config.latest_pypi_version != installed_version
    )

    return EmailSearchInfo(
        tool="mailcat",
        version=installed_version,
        provider_count=_active_provider_count(config),
        latest_version=config.latest_pypi_version,
        update_available=update_available if config.latest_pypi_version else None,
    )


@router.post(
    "/check-update",
    response_model=EmailSearchInfo,
    summary="Check PyPI for a mailcat-osint update",
    description="Check PyPI for the latest published mailcat-osint version. Doesn't install anything - "
    "a newer version still requires a container rebuild, this only checks what's available.",
)
async def check_update(db: SessionDep) -> EmailSearchInfo:
    """Manually check PyPI for a newer mailcat-osint release"""
    latest_version = await fetch_latest_pypi_version()
    config = await record_pypi_check(db, latest_version)
    installed_version = get_installed_version()

    return EmailSearchInfo(
        tool="mailcat",
        version=installed_version,
        provider_count=_active_provider_count(config),
        latest_version=config.latest_pypi_version,
        update_available=bool(config.latest_pypi_version) and config.latest_pypi_version != installed_version,
    )


@router.get(
    "/runs",
    response_model=list[SearchRunSummary],
    summary="List past searches",
    description="Retrieve past and in-progress email searches, most recent first",
)
async def read_search_runs(db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100) -> list[SearchRunSummary]:
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
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search run not found", error_code="EMAIL_SEARCH_RUN_NOT_FOUND")
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
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search run not found", error_code="EMAIL_SEARCH_RUN_NOT_FOUND")
    logger.info("Deleted email search run %s", search_id)
