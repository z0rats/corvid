from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns, make_scan_history_crud
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.username_search.models.username_search_models import (
    MaigretSearch,
    MaigretSiteResult,
)

# Shared by all three username_search sources (maigret/social_analyzer/
# threat_actor_usernames all target this same table) - passed to ScanRun.execute()
# by each source's service module, which now owns row create/complete/cancel/fail
# directly via core/scans/crud.py.
SCAN_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")

_history = make_scan_history_crud(
    MaigretSearch, MaigretSearch.started_at, relation=MaigretSearch.site_results
)
list_search_runs = _history.list
get_search_run = _history.get
get_search_run_with_results = _history.get_with_results
delete_search_run = _history.delete


async def add_site_results(db: AsyncSession, search_id: int, found_sites: list[dict]) -> None:
    """Persist found-site child rows for a search run. Called by each source's
    own run_work once it has results (on both normal completion and mid-scan
    cancellation) - ScanRun's generic mark_completed/mark_cancelled only ever
    touch scalar columns on the parent row, never these child rows."""
    for site in found_sites:
        db.add(
            MaigretSiteResult(
                search_id=search_id,
                site_name=site["site_name"],
                url_user=site["url_user"],
                http_status=site.get("http_status"),
                extra=site.get("extra"),
            )
        )
    await db.flush()


async def interrupt_running_search_runs(db: AsyncSession) -> int:
    """Mark any run still 'running' as failed - see `mark_stale_running_as_failed`'s
    docstring for why this is needed (an in-memory asyncio task doesn't survive
    a process restart)."""
    return await mark_stale_running_as_failed(
        db,
        MaigretSearch,
        error_column=SCAN_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=SCAN_COLUMNS.completed_at_column,
    )
