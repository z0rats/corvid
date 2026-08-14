"""Shared start -> run -> terminal lifecycle for every SSE-streamed scan feature.

Each of the five scan-style call sites (username_search's maigret/social_analyzer/
threat_actor_usernames sources, email_search, git_recon) used to hand-roll the same
skeleton: create a 'running' row, emit a 'started' event, run its own scan
coroutine, then on success/CancelledError/exception mark the row completed/
cancelled/failed and emit the matching terminal event, deregister its cancel
handle, and push the SSE sentinel. `ScanRun.execute()` is that skeleton; only the
feature-specific scan logic (and its own progress events) is now unique to each
service, expressed as a `run_work` coroutine the feature supplies.
"""

import asyncio
import dataclasses
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from app.core.database import managed_session
from app.core.scans.crud import (
    ScanColumns,
    create_running,
    mark_cancelled,
    mark_completed,
    mark_failed,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ScanEvent:
    """One SSE-bound scan event. Serialized on the wire as the nested
    `{"type": ..., "data": {...}}` shape (see `core/scans/sse.py`'s `queue_sink`),
    replacing every feature's previous flat `{"type": ..., "search_id": ..., ...}`
    dict."""

    type: Literal["started", "progress", "completed", "cancelled", "failed"]
    data: dict[str, Any]


class Cancellable:
    """Protocol every scan-cancellation adapter implements (see `cancellable.py`
    for the concrete `TaskCancellable`/`ProcessCancellable`/`GitCloneCancellable`).

    `cancel()` must wait for the underlying work to actually stop, not just send
    a signal and return - callers (in particular `ScanRun.cancel()`, driven from
    a cancel HTTP endpoint) rely on it to know the scan has genuinely wound down
    before reporting success.
    """

    async def cancel(self) -> None: ...


@dataclasses.dataclass
class ScanOutcome:
    """What a `run_work` coroutine returns on success, or attaches to a raised
    `ScanCancelled` when it has partial results worth reporting.

    `fields` are scalar columns applied to *both* the DB row (via `mark_completed`/
    `mark_cancelled`'s `**fields`) and the terminal event's `data` (e.g.
    `total_sites_checked`/`found_count`) - every feature's completed/cancelled
    event has so far carried exactly the same fields it persists. `db_only_fields`
    covers the rare exception (git_recon's full `result` JSON blob, persisted but
    never echoed on the wire - the frontend re-fetches it via history/runs
    endpoints instead).

    `persist_children`, if given, is called with the same session and inside the
    same transaction as the `mark_completed`/`mark_cancelled` call that follows it
    - so a found-site/found-provider child-row insert and the parent row's status
    flip commit together atomically, rather than as two separate transactions
    (username_search/email_search/threat_actor_usernames all use this; git_recon
    has no child rows and leaves it unset).
    """

    fields: dict[str, Any] = dataclasses.field(default_factory=dict)
    db_only_fields: dict[str, Any] = dataclasses.field(default_factory=dict)
    persist_children: Callable[[Any], Awaitable[None]] | None = None


class ScanCancelled(Exception):
    """Raise from `run_work` instead of letting a bare `asyncio.CancelledError`
    propagate, when there are partial results worth persisting/reporting on
    cancellation (sites checked so far, etc). `ScanRun.execute()` treats a bare
    `asyncio.CancelledError` the same way, just with an empty `ScanOutcome` -
    features with nothing partial to report (whose Cancellable never actually
    cancels the running asyncio task, e.g. git_recon) don't need this at all.
    """

    def __init__(self, outcome: ScanOutcome | None = None):
        super().__init__()
        self.outcome = outcome if outcome is not None else ScanOutcome()


RunWork = Callable[[int], Awaitable[ScanOutcome]]
OnEvent = Callable[[ScanEvent | None], None]


class ScanRun:
    """Drives one scan's lifecycle end to end and tracks its `Cancellable` (if
    any) in a process-local registry keyed by `(feature_name, search_id)`, so a
    separate request can cancel it via `ScanRun.cancel()`. Namespacing the
    registry by `feature_name` (not just `search_id`) matters because each
    scan-style model has its own independently-incrementing primary key - two
    different features can otherwise share the same numeric search_id at once.
    """

    _registry: dict[tuple[str, int], Cancellable] = {}

    @classmethod
    async def execute(
        cls,
        feature_name: str,
        model: type,
        run_work: RunWork,
        on_event: OnEvent,
        *,
        columns: ScanColumns,
        create_fields: dict[str, Any],
        started_fields: dict[str, Any] | None = None,
        cancellable: Cancellable | None = None,
        expected_exceptions: tuple[type[Exception], ...] = (),
    ) -> None:
        """Create the running row, emit `started`, run `run_work(search_id)`,
        then mark the row and emit the matching terminal event - regardless of
        which of the five scan call sites is driving it.

        `columns`/`create_fields` are required (beyond the terse `model`) since
        actually creating and marking the row needs them; `started_fields` is
        the extra feature-specific data (username, mode/target, ...) merged into
        the `started` event alongside `search_id`. `expected_exceptions` are
        failure modes a feature already gives a clear, user-facing message for
        (bad input, a timeout it already renamed) - logged at `warning` without
        a traceback instead of `error` with one, so routine cases (e.g. a typo'd
        git_recon target) don't read as application errors in the logs.
        """
        async with managed_session() as db:
            search = await create_running(db, model, **create_fields)
            search_id = search.id

        key = (feature_name, search_id)
        if cancellable is not None:
            cls._registry[key] = cancellable

        on_event(ScanEvent("started", {"search_id": search_id, **(started_fields or {})}))

        try:
            try:
                outcome = await run_work(search_id)
            except ScanCancelled as exc:
                async with managed_session() as db:
                    if exc.outcome.persist_children:
                        await exc.outcome.persist_children(db)
                    await mark_cancelled(
                        db,
                        model,
                        search_id,
                        columns=columns,
                        **exc.outcome.fields,
                        **exc.outcome.db_only_fields,
                    )
                on_event(ScanEvent("cancelled", {"search_id": search_id, **exc.outcome.fields}))
                return
            except asyncio.CancelledError:
                async with managed_session() as db:
                    await mark_cancelled(db, model, search_id, columns=columns)
                on_event(ScanEvent("cancelled", {"search_id": search_id}))
                raise
            except Exception as exc:
                if isinstance(exc, expected_exceptions):
                    logger.warning("%s scan %s failed: %s", feature_name, search_id, exc)
                else:
                    logger.error(
                        "%s scan %s failed: %s", feature_name, search_id, exc, exc_info=True
                    )
                async with managed_session() as db:
                    await mark_failed(db, model, search_id, columns=columns, error_message=str(exc))
                on_event(ScanEvent("failed", {"search_id": search_id, "error": str(exc)}))
                return

            async with managed_session() as db:
                if outcome.persist_children:
                    await outcome.persist_children(db)
                await mark_completed(
                    db,
                    model,
                    search_id,
                    columns=columns,
                    **outcome.fields,
                    **outcome.db_only_fields,
                )
            on_event(ScanEvent("completed", {"search_id": search_id, **outcome.fields}))
        finally:
            cls._registry.pop(key, None)
            on_event(None)

    @classmethod
    async def cancel(cls, feature_name: str, search_id: int) -> bool:
        """Request cancellation of a currently-running scan. Returns False if no
        scan with that (feature, id) is currently running (already finished, or
        never existed). Awaits the adapter's own `cancel()`, so this only
        returns once the underlying work has actually stopped (except
        git_recon's `GitCloneCancellable`, which deliberately doesn't wait for
        its worker thread to finish - see its own docstring)."""
        cancellable = cls._registry.get((feature_name, search_id))
        if cancellable is None:
            return False
        await cancellable.cancel()
        return True
