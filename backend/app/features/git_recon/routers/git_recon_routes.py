import asyncio
import json
import logging

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.features.git_recon.crud.git_recon_crud import delete_search, get_search, list_searches
from app.features.git_recon.schemas.git_recon_schemas import ScanRequest, SearchDetail, SearchSummary
from app.features.git_recon.service.git_recon_service import run_scan_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/git-recon", tags=["Git Recon"])


async def _get_github_token(db: AsyncSession) -> str | None:
    """Reuse the GitHub PAT already configured under Settings > API Keys, rather
    than introducing a separate credential just for this feature."""
    apikey = await get_apikey(db=db, name="github_pat")
    if apikey and apikey.is_active and apikey.key:
        return apikey.key
    return None


@router.post(
    "/scan",
    summary="Correlate git/GitHub identities for a target",
    description="Run a gitcolombo scan: 'search' queries GitHub's API only (GPG-key UIDs + "
    "commit search) for a username; 'url'/'nickname' clone one repo or every public repo of a "
    "user/org and correlate author/committer identities across their commit history. Streams "
    "progress as Server-Sent Events - a scan can run for several minutes (full, non-shallow "
    "clones), too long to hold open as a single request behind most reverse proxies.",
)
@limiter.limit("5/minute")
async def scan(request: Request, db: SessionDep, scan_request: ScanRequest):
    github_token = await _get_github_token(db)

    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(run_scan_task(
        mode=scan_request.mode,
        target=scan_request.target,
        include_forks=scan_request.include_forks,
        resolve_github_logins=scan_request.resolve_github_logins,
        ignore_noreply=scan_request.ignore_noreply,
        github_token=github_token,
        queue=queue,
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


@router.get(
    "/history",
    response_model=list[SearchSummary],
    summary="List past git recon searches",
    description="List past git/GitHub identity-correlation searches, most recent first",
)
async def read_searches(db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100) -> list[SearchSummary]:
    searches = await list_searches(db, skip=skip, limit=limit)
    return [SearchSummary.model_validate(s) for s in searches]


@router.get(
    "/history/{search_id}",
    response_model=SearchDetail,
    summary="Get a past git recon search",
    description="Get a past git/GitHub identity-correlation search, including its full result",
    responses={404: {"description": "Search not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> SearchDetail:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="GIT_RECON_NOT_FOUND")
    return SearchDetail.model_validate(search)


@router.delete(
    "/history/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a git recon search",
    description="Permanently delete a past git recon search",
    responses={404: {"description": "Search not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="GIT_RECON_NOT_FOUND")
    logger.info("Deleted git recon search %s", search_id)
