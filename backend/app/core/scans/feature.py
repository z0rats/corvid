from dataclasses import dataclass
from functools import cached_property
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns, make_scan_history_crud
from app.core.scans.reconciliation import mark_stale_running_as_failed
from app.core.scans.run import OnEvent, RunWork, ScanRun

INTERRUPTED_MESSAGE = "Interrupted by server restart"


@dataclass(frozen=True)
class ScanFeature:
    """One scan-style feature's persisted runs: its table and everything the shared
    lifecycle needs to know about it, declared once.

    - `execute` drives a run (`ScanRun.execute` with this table/columns filled in);
      `name` is the default alert/log name - a table written by several sources
      (username_search) passes its own per run.
    - `cancel` stops a running run by id alone - ids are unique per table.
    - `history` is the list/get/get_with_results/delete quartet.
    - `target_column` names the column holding what the run was about (username, domain,
      ...) - read by `recent_activity` for the cross-feature activity feed.
    - `interrupt_running` marks runs left 'running' by a previous process as failed;
      every instance must be listed in `app/utils/scan_reconciliation_registry.py`
      (enforced by `tests/core/test_scan_reconciliation_coverage.py`).
    """

    name: str
    model: type
    columns: ScanColumns
    order_by: Any
    target_column: str
    relation: Any = None

    @cached_property
    def history(self) -> SimpleNamespace:
        return make_scan_history_crud(self.model, self.order_by, relation=self.relation)

    async def execute(
        self, run_work: RunWork, on_event: OnEvent, *, name: str | None = None, **kwargs: Any
    ) -> None:
        await ScanRun.execute(
            name or self.name, self.model, run_work, on_event, columns=self.columns, **kwargs
        )

    async def cancel(self, search_id: int) -> bool:
        return await ScanRun.cancel(self.model, search_id)

    async def interrupt_running(self, db: AsyncSession) -> int:
        return await mark_stale_running_as_failed(
            db,
            self.model,
            error_column=self.columns.error_column,
            error_message=INTERRUPTED_MESSAGE,
            completed_at_column=self.columns.completed_at_column,
        )

    async def recent_activity(self, db: AsyncSession, limit: int) -> list[dict[str, Any]]:
        """This feature's newest runs as plain activity-feed rows, newest first."""
        model: Any = self.model
        target = getattr(model, self.target_column)
        rows = await db.execute(
            select(model.id, target, model.status, self.order_by)
            .order_by(self.order_by.desc())
            .limit(limit)
        )
        return [
            {
                "feature": self.name,
                "id": id_,
                "target": target_value,
                "status": status,
                "timestamp": ts,
            }
            for id_, target_value, status, ts in rows.all()
        ]
