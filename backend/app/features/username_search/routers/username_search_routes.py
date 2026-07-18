import asyncio
import json
import logging

import maigret
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import StreamingResponse

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.settings.username_search.crud.social_analyzer_settings_crud import (
    get_social_analyzer_config,
    record_pypi_check as record_social_analyzer_pypi_check,
)
from app.core.settings.username_search.crud.username_search_settings_crud import (
    get_username_search_config,
    record_pypi_check as record_maigret_pypi_check,
)
from app.features.username_search.config.maigret_config import (
    fetch_latest_pypi_version as fetch_latest_maigret_pypi_version,
    get_available_tags,
    get_maigret_database,
)
from app.features.username_search.config.social_analyzer_config import (
    fetch_latest_pypi_version as fetch_latest_social_analyzer_pypi_version,
    get_bundled_site_count,
    get_installed_version as get_social_analyzer_version,
)
from app.features.username_search.crud.username_search_crud import (
    delete_search_run,
    get_search_run_with_results,
    list_search_runs,
)
from app.features.username_search.schemas.username_search_schemas import (
    ScanRequest,
    SearchRunDetail,
    SearchRunSummary,
    UsernameSearchInfo,
)
from app.features.username_search.service.db_refresh_service import refresh_database
from app.features.username_search.service.report_service import (
    delete_scan_results,
    generate_export,
    has_scan_results,
    load_scan_results,
)
from app.features.username_search.service.social_analyzer_service import (
    cancel_scan as cancel_social_analyzer_scan,
    run_scan as run_social_analyzer_scan,
)
from app.features.username_search.service.username_search_service import cancel_scan as cancel_maigret_scan, run_scan as run_maigret_scan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/username-search", tags=["Username Search"])


@router.post(
    "/scan",
    summary="Start a username search",
    description="Start a username search (Maigret or social-analyzer), streaming progress as Server-Sent Events",
)
@limiter.limit("3/minute")
async def start_scan(request: Request, scan_request: ScanRequest):
    """Start a new username search and stream its progress"""
    logger.info("Starting %s username search for '%s'", scan_request.source, scan_request.username)

    queue: asyncio.Queue = asyncio.Queue()
    if scan_request.source == "social_analyzer":
        asyncio.create_task(run_social_analyzer_scan(scan_request.username, queue))
    else:
        asyncio.create_task(run_maigret_scan(
            scan_request.username,
            queue,
            tags=scan_request.tags,
            excluded_tags=scan_request.excluded_tags,
        ))

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
    description="Cancel a currently-running username search, keeping whatever sites were found before cancellation",
    responses={404: {"description": "No running search with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    """Cancel a running scan, regardless of which source is running it"""
    cancelled = cancel_maigret_scan(search_id) or cancel_social_analyzer_scan(search_id)
    if not cancelled:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No running search with that ID", error_code="USERNAME_SEARCH_NOT_RUNNING")
    logger.info("Cancellation requested for username search run %s", search_id)


@router.get(
    "/tags",
    response_model=list[str],
    summary="List available site tags",
    description="List all site category tags in the database that can be used to filter a search",
)
async def read_available_tags() -> list[str]:
    """List available site tags for filtering"""
    return get_available_tags()


@router.get(
    "/info",
    response_model=list[UsernameSearchInfo],
    summary="Get search tools info",
    description="Get each underlying search tool's name, version, and site database freshness",
)
async def read_info(db: ReadSessionDep) -> list[UsernameSearchInfo]:
    """Get info about both search tools and their site databases"""
    maigret_config = await get_username_search_config(db)
    maigret_site_count = maigret_config.db_site_count or len(get_maigret_database().sites)
    maigret_update_available = (
        bool(maigret_config.latest_pypi_version) and maigret_config.latest_pypi_version != maigret.__version__
    )

    sa_config = await get_social_analyzer_config(db)
    sa_update_available = (
        bool(sa_config.latest_pypi_version) and sa_config.latest_pypi_version != get_social_analyzer_version()
    )

    return [
        UsernameSearchInfo(
            tool="maigret",
            version=maigret.__version__,
            site_count=maigret_site_count,
            db_last_updated_at=maigret_config.db_last_updated_at,
            latest_version=maigret_config.latest_pypi_version,
            update_available=maigret_update_available if maigret_config.latest_pypi_version else None,
        ),
        UsernameSearchInfo(
            tool="social_analyzer",
            version=get_social_analyzer_version(),
            site_count=get_bundled_site_count(),
            latest_version=sa_config.latest_pypi_version,
            update_available=sa_update_available if sa_config.latest_pypi_version else None,
        ),
    ]


@router.post(
    "/refresh-db",
    response_model=UsernameSearchInfo,
    summary="Refresh the Maigret site database now",
    description="Force-check for and download a Maigret site database update, bypassing the scheduled interval",
)
async def refresh_db_endpoint(db: SessionDep) -> UsernameSearchInfo:
    """Manually trigger a Maigret site database refresh"""
    site_count = await refresh_database(db, force=True)
    config = await get_username_search_config(db)
    return UsernameSearchInfo(
        tool="maigret",
        version=maigret.__version__,
        site_count=site_count,
        db_last_updated_at=config.db_last_updated_at,
    )


@router.post(
    "/social-analyzer/check-update",
    response_model=UsernameSearchInfo,
    summary="Check PyPI for a social-analyzer update",
    description="Check PyPI for the latest published social-analyzer version. Doesn't install anything - "
    "a newer version still requires a container rebuild, since site data ships inside the pip package.",
)
async def check_social_analyzer_update(db: SessionDep) -> UsernameSearchInfo:
    """Manually check PyPI for a newer social-analyzer release"""
    latest_version = await fetch_latest_social_analyzer_pypi_version()
    config = await record_social_analyzer_pypi_check(db, latest_version)
    installed_version = get_social_analyzer_version()
    return UsernameSearchInfo(
        tool="social_analyzer",
        version=installed_version,
        site_count=get_bundled_site_count(),
        latest_version=config.latest_pypi_version,
        update_available=bool(config.latest_pypi_version) and config.latest_pypi_version != installed_version,
    )


@router.post(
    "/maigret/check-update",
    response_model=UsernameSearchInfo,
    summary="Check PyPI for a maigret update",
    description="Check PyPI for the latest published maigret version. Doesn't install anything - "
    "a newer version still requires a container rebuild, since maigret is installed at image-build time.",
)
async def check_maigret_update(db: SessionDep) -> UsernameSearchInfo:
    """Manually check PyPI for a newer maigret release"""
    latest_version = await fetch_latest_maigret_pypi_version()
    config = await record_maigret_pypi_check(db, latest_version)
    site_count = config.db_site_count or len(get_maigret_database().sites)
    return UsernameSearchInfo(
        tool="maigret",
        version=maigret.__version__,
        site_count=site_count,
        db_last_updated_at=config.db_last_updated_at,
        latest_version=config.latest_pypi_version,
        update_available=bool(config.latest_pypi_version) and config.latest_pypi_version != maigret.__version__,
    )


@router.get(
    "/runs",
    response_model=list[SearchRunSummary],
    summary="List past searches",
    description="Retrieve past and in-progress username searches, most recent first",
)
async def read_search_runs(db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100) -> list[SearchRunSummary]:
    """List past search runs with pagination"""
    runs = await list_search_runs(db, skip=skip, limit=limit)
    return [SearchRunSummary.model_validate(r) for r in runs]


@router.get(
    "/runs/{search_id}",
    response_model=SearchRunDetail,
    summary="Get search run detail",
    description="Retrieve a specific search run including its found-site results",
    responses={404: {"description": "Search run not found"}},
)
async def read_search_run(search_id: int, db: ReadSessionDep) -> SearchRunDetail:
    """Get a specific search run with its found sites"""
    run = await get_search_run_with_results(db, search_id)
    if not run:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search run not found", error_code="USERNAME_SEARCH_RUN_NOT_FOUND")
    detail = SearchRunDetail.model_validate(run)
    detail.has_export = has_scan_results(search_id)
    return detail


@router.get(
    "/runs/{search_id}/export/{export_format}",
    summary="Export a search run's report",
    description="Download the full per-site report (found and not-found) in the given format, generated by Maigret's own report writers",
    responses={404: {"description": "Search run or report not found"}, 400: {"description": "Unsupported export format"}},
)
async def export_search_run(search_id: int, export_format: str, db: ReadSessionDep) -> Response:
    """Export a search run's full report in the given format"""
    run = await get_search_run_with_results(db, search_id)
    if not run:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search run not found", error_code="USERNAME_SEARCH_RUN_NOT_FOUND")

    results = load_scan_results(search_id)
    if results is None:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No report available for this search run", error_code="USERNAME_SEARCH_REPORT_NOT_FOUND")

    try:
        content, media_type, filename = generate_export(search_id, run.username, results, export_format)
    except ValueError as exc:
        raise AppHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc), error_code="USERNAME_SEARCH_UNSUPPORTED_FORMAT") from exc

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/runs/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete search run",
    description="Permanently delete a search run and its found-site results",
    responses={404: {"description": "Search run not found"}},
)
async def delete_search_run_endpoint(search_id: int, db: SessionDep) -> None:
    """Delete a specific search run"""
    run = await delete_search_run(db, search_id)
    if not run:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search run not found", error_code="USERNAME_SEARCH_RUN_NOT_FOUND")
    delete_scan_results(search_id)
    logger.info("Deleted username search run %s", search_id)
