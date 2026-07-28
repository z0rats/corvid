import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


async def mark_stale_running_as_failed(
    db: AsyncSession,
    model: type,
    *,
    error_column: str,
    error_message: str,
    completed_at_column: str | None,
) -> int:
    """Mark any row of `model` still `status == "running"` as `failed`.

    Called once per scan-style feature (username_search, email_search, git_recon)
    from `main.py`'s `_reconcile_stale_scans()` on startup: each scan is driven by
    an in-memory `asyncio.Task`, so it doesn't survive a process restart - without
    this, a run interrupted by a container stop/crash would stay 'running' forever
    and the frontend would have no way to tell it apart from one still in progress.

    `error_column`/`completed_at_column` are explicit, required parameters (not
    introspected via `hasattr`) since the three models don't agree on naming -
    `GitReconSearch.error` vs `MaigretSearch`/`MailSearch`'s `error_message`, and
    `GitReconSearch` has no `completed_at` column at all (pass `None` for it).
    """
    values: dict = {"status": "failed", error_column: error_message}
    if completed_at_column is not None:
        values[completed_at_column] = datetime.datetime.now(datetime.timezone.utc)

    result = await db.execute(
        update(model).where(model.status == "running").values(**values)
    )
    await db.flush()
    return result.rowcount
