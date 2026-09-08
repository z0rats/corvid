from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns, make_scan_history_crud
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.git_recon.models.git_recon_models import GitReconSearch

# ScanRun.execute() now owns row create/complete/cancel/fail directly via
# core/scans/crud.py, using this. GitReconSearch has no completed_at column and
# names its error column `error` (not `error_message`, unlike the other two
# scan-style models).
SCAN_COLUMNS = ScanColumns(error_column="error", completed_at_column=None)

# No `relation` - GitReconSearch's results are a JSON blob column, not a child
# table (see ADR-0002), so there's nothing to eager-load.
_history = make_scan_history_crud(GitReconSearch, GitReconSearch.searched_at)
list_searches = _history.list
get_search = _history.get
delete_search = _history.delete


async def interrupt_running_searches(db: AsyncSession) -> int:
    """Mark any search still 'running' as failed - see `mark_stale_running_as_failed`'s
    docstring for why this is needed (an in-memory asyncio task doesn't survive
    a process restart)."""
    return await mark_stale_running_as_failed(
        db,
        GitReconSearch,
        error_column=SCAN_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=SCAN_COLUMNS.completed_at_column,
    )
