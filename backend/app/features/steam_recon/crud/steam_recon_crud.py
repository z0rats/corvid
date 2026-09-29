from app.core.scans.crud import ScanColumns, make_scan_history_crud
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.features.steam_recon.models.steam_recon_models import SteamReconSearch

# No child-row table (see the model's docstring) - `relation` is left unset, same as git_recon.
SCAN_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")

_history = make_scan_history_crud(SteamReconSearch, SteamReconSearch.started_at)
list_searches = _history.list
get_search = _history.get
get_search_with_result = _history.get_with_results
delete_search = _history.delete


async def interrupt_running_searches(db) -> int:
    """Mark any scan still 'running' as failed on startup - an in-memory asyncio task doesn't
    survive a process restart (see `mark_stale_running_as_failed`'s docstring)."""
    return await mark_stale_running_as_failed(
        db,
        SteamReconSearch,
        error_column=SCAN_COLUMNS.error_column,
        error_message="Interrupted by server restart",
        completed_at_column=SCAN_COLUMNS.completed_at_column,
    )
