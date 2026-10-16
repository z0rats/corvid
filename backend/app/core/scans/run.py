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

from app.core.alerts.service.alerts_service import TelegramCategory, raise_alert
from app.core.config.settings import settings
from app.core.database import managed_session
from app.core.scans.crud import (
    ScanColumns,
    create_running,
    mark_cancelled,
    mark_completed,
    mark_failed,
)

logger = logging.getLogger(__name__)

# Caps resource-heavy scans across every feature (`heavy=True` runs); per event loop, since an
# asyncio.Semaphore binds to the first loop that waits on it (tests run one loop per test).
_heavy_slots: tuple[asyncio.AbstractEventLoop, asyncio.Semaphore] | None = None


def _heavy_semaphore() -> asyncio.Semaphore:
    global _heavy_slots
    loop = asyncio.get_running_loop()
    if _heavy_slots is None or _heavy_slots[0] is not loop:
        _heavy_slots = (loop, asyncio.Semaphore(settings.scans.max_concurrent_heavy))
    return _heavy_slots[1]


def _format_fields(fields: dict[str, Any]) -> str:
    """Best-effort human-readable rendering of a scan's create/outcome fields
    for a notification message - generic on purpose, so every current and
    future `ScanRun`-based feature is covered without a per-feature template."""
    return ", ".join(f"{key}={value}" for key, value in fields.items() if value not in (None, ""))


async def _notify_terminal(
    db,
    feature_name: str,
    search_id: int,
    create_fields: dict[str, Any],
    *,
    title_verb: str,
    message_verb: str,
    detail: str = "",
    extra_fields: dict[str, Any] | None = None,
    telegram_category: TelegramCategory,
) -> None:
    """Raise the "scan <verb>" alert shared by every terminal branch of
    `ScanRun.execute()` below - only the wording, an optional trailing detail
    (e.g. the exception on failure), and the outcome's own extra fields differ
    between cancelled/failed/completed."""
    extra = f" — {_format_fields(extra_fields)}" if extra_fields else ""
    suffix = f": {detail}" if detail else f"{extra}."
    await raise_alert(
        db,
        feature_name,
        f"{feature_name}: scan {title_verb}",
        f"Scan #{search_id} ({_format_fields(create_fields)}) {message_verb}{suffix}",
        telegram_category=telegram_category,
    )


@dataclasses.dataclass
class ScanEvent:
    """One SSE-bound scan event. Serialized on the wire as the nested
    `{"type": ..., "data": {...}}` shape (see `core/scans/sse.py`'s `queue_sink`),
    replacing every feature's previous flat `{"type": ..., "search_id": ..., ...}`
    dict."""

    type: Literal["started", "queued", "running", "progress", "completed", "cancelled", "failed"]
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
    any) in a process-local registry keyed by `(model, search_id)`, so a
    separate request can cancel it via `ScanRun.cancel()`. Keyed by the row's
    table (not a feature name) because a search_id is unique exactly per table:
    two tables can share a numeric id at once, while several sources writing to
    one table (username_search's three) never can - so cancelling a run needs
    only its table and id, never which source started it.
    """

    _registry: dict[tuple[type, int], Cancellable] = {}
    # Heavy runs still waiting for a slot, so `cancel()` can drop one from the queue before its
    # work (and its subprocess, if any) ever starts.
    _queued: dict[tuple[type, int], asyncio.Future] = {}

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
        heavy: bool = False,
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

        `heavy` runs share `SCAN_MAX_CONCURRENT_HEAVY` slots: past the cap, a run emits
        `queued` and waits (cancellable) before `run_work` starts, then `running` once it
        gets a slot. A heavy feature must therefore start its real work (subprocesses
        included) inside `run_work`, not before calling this.
        """
        async with managed_session() as db:
            search = await create_running(db, model, **create_fields)
            search_id = search.id

        key = (model, search_id)
        if cancellable is not None:
            cls._registry[key] = cancellable

        on_event(ScanEvent("started", {"search_id": search_id, **(started_fields or {})}))

        slot: asyncio.Semaphore | None = None
        try:
            try:
                if heavy:
                    slot = await cls._acquire_heavy_slot(key, search_id, on_event)
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
                    await _notify_terminal(
                        db,
                        feature_name,
                        search_id,
                        create_fields,
                        title_verb="cancelled",
                        message_verb="was cancelled",
                        extra_fields=exc.outcome.fields,
                        telegram_category="scan_finished",
                    )
                on_event(ScanEvent("cancelled", {"search_id": search_id, **exc.outcome.fields}))
                return
            except asyncio.CancelledError:
                async with managed_session() as db:
                    await mark_cancelled(db, model, search_id, columns=columns)
                    await _notify_terminal(
                        db,
                        feature_name,
                        search_id,
                        create_fields,
                        title_verb="cancelled",
                        message_verb="was cancelled",
                        telegram_category="scan_finished",
                    )
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
                    await _notify_terminal(
                        db,
                        feature_name,
                        search_id,
                        create_fields,
                        title_verb="failed",
                        message_verb="failed",
                        detail=str(exc),
                        telegram_category="scan_failed",
                    )
                # Only expected (validation/upstream) failures carry their message to the
                # client; an unexpected exception's text may expose internals.
                client_error = str(exc) if isinstance(exc, expected_exceptions) else "Scan failed"
                on_event(ScanEvent("failed", {"search_id": search_id, "error": client_error}))
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
                await _notify_terminal(
                    db,
                    feature_name,
                    search_id,
                    create_fields,
                    title_verb="completed",
                    message_verb="completed",
                    extra_fields=outcome.fields,
                    telegram_category="scan_finished",
                )
            on_event(ScanEvent("completed", {"search_id": search_id, **outcome.fields}))
        finally:
            if slot is not None:
                slot.release()
            cls._registry.pop(key, None)
            on_event(None)

    @classmethod
    async def _acquire_heavy_slot(
        cls, key: tuple[type, int], search_id: int, on_event: OnEvent
    ) -> asyncio.Semaphore:
        """Wait for a heavy-scan slot and return the semaphore it must be released to.
        Raises `ScanCancelled` if `cancel()` drops this run from the queue."""
        slots = _heavy_semaphore()
        queued = slots.locked()
        if queued:
            on_event(ScanEvent("queued", {"search_id": search_id}))

        waiter = asyncio.ensure_future(slots.acquire())
        cls._queued[key] = waiter
        try:
            await waiter
        except asyncio.CancelledError:
            # The slot may have been granted just before this task was cancelled.
            if waiter.done() and not waiter.cancelled():
                slots.release()
            current = asyncio.current_task()
            if current is not None and current.cancelling():
                raise  # the whole scan task was cancelled, not just its queue wait
            raise ScanCancelled() from None
        finally:
            cls._queued.pop(key, None)

        if queued:
            on_event(ScanEvent("running", {"search_id": search_id}))
        return slots

    @classmethod
    def is_queued(cls, model: type, search_id: int) -> bool:
        """Whether this heavy run is still waiting for a slot. Queued-ness lives only here, in
        memory - the row itself already says `running` from the moment it's created."""
        return (model, search_id) in cls._queued

    @classmethod
    async def cancel(cls, model: type, search_id: int) -> bool:
        """Request cancellation of a currently-running scan. Returns False if no
        scan with that (table, id) is currently running (already finished, or
        never existed). Awaits the adapter's own `cancel()`, so this only
        returns once the underlying work has actually stopped (except
        git_recon's `GitCloneCancellable`, which deliberately doesn't wait for
        its worker thread to finish - see its own docstring)."""
        waiter = cls._queued.get((model, search_id))
        if waiter is not None and waiter.cancel():
            return True  # still queued: nothing started yet, so nothing else to stop
        cancellable = cls._registry.get((model, search_id))
        if cancellable is None:
            return False
        await cancellable.cancel()
        return True
