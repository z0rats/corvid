import asyncio
import logging

from fastapi import APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import SessionDep
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.features.git_recon.crud.git_recon_crud import GIT_RECON_SCANS
from app.features.git_recon.schemas.git_recon_schemas import (
    ScanRequest,
    SearchDetail,
    SearchSummary,
)
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
    asyncio.create_task(
        run_scan_task(
            mode=scan_request.mode,
            target=scan_request.target,
            include_forks=scan_request.include_forks,
            resolve_github_logins=scan_request.resolve_github_logins,
            ignore_noreply=scan_request.ignore_noreply,
            github_token=github_token,
            queue=queue,
        )
    )

    return sse_response(queue)


add_run_routes(
    router,
    GIT_RECON_SCANS,
    display_name="git recon",
    summary_schema=SearchSummary,
    detail_schema=SearchDetail,
    not_found_code="GIT_RECON_NOT_FOUND",
)
