import logging

from fastapi import APIRouter, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.features.git_recon.crud.git_recon_crud import (
    create_search,
    delete_search,
    get_search,
    list_searches,
)
from app.features.git_recon.schemas.git_recon_schemas import (
    ScanRequest,
    ScanResponse,
    SearchDetail,
    SearchSummary,
)
from app.features.git_recon.service.git_recon_service import GitReconError, run_scan

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
    response_model=ScanResponse,
    summary="Correlate git/GitHub identities for a target",
    description="Run a gitcolombo scan: 'search' queries GitHub's API only (GPG-key UIDs + "
    "commit search) for a username; 'url'/'nickname' clone one repo or every public repo of a "
    "user/org and correlate author/committer identities across their commit history",
    responses={400: {"description": "Invalid target for the given mode, or nothing to scan"}},
)
@limiter.limit("5/minute")
async def scan(request: Request, db: SessionDep, scan_request: ScanRequest) -> ScanResponse:
    github_token = await _get_github_token(db)

    try:
        result = await run_scan(
            mode=scan_request.mode,
            target=scan_request.target,
            include_forks=scan_request.include_forks,
            resolve_github_logins=scan_request.resolve_github_logins,
            ignore_noreply=scan_request.ignore_noreply,
            github_token=github_token,
        )
    except GitReconError as exc:
        raise AppHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc), error_code="GIT_RECON_INVALID_TARGET",
        ) from exc
    except TimeoutError as exc:
        raise AppHTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Scan timed out", error_code="GIT_RECON_TIMEOUT",
        ) from exc

    repo_outcomes = result.get("repos", [])
    search = await create_search(
        db,
        mode=scan_request.mode,
        target=scan_request.target,
        status="completed",
        error=None,
        repos_scanned=sum(1 for r in repo_outcomes if r["cloned"]),
        repos_failed=sum(1 for r in repo_outcomes if not r["cloned"]),
        persons_found=len(result.get("persons", [])),
        result=result,
    )

    logger.info(
        "Git recon %s scan for '%s': %d person(s), %d repo(s) scanned",
        search.mode, search.target, search.persons_found, search.repos_scanned,
    )

    return ScanResponse(
        search_id=search.id, mode=search.mode, target=search.target, status=search.status,
        error=search.error, result=result,
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
