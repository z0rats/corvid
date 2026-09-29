# Scan-style feature lifecycle (`core/scans/`)

Deep-dive referenced from AGENTS.md's Conventions section. Shared by every SSE-streamed,
cancellable/resumable, persisted-history feature: `username_search`'s three sources,
`email_search`, `git_recon`, `ru_business_check`.

## Backend: `core/scans/run.py`'s `ScanRun`

`execute()`:
1. Creates the running row.
2. Emits a `started` `ScanEvent`.
3. Runs the feature's own `run_work(search_id)` coroutine, which emits its own `progress` events
   and returns a `ScanOutcome`.
4. Marks the row completed/cancelled/failed and emits the matching terminal event.

Wire shape is the nested `{"type": ..., "data": {...}}`, adapted onto the raw `asyncio.Queue`
`sse_response` reads from (queue → `StreamingResponse`) via `core/scans/sse.py`'s `queue_sink`.

## Cancellation

`ScanRun.cancel(feature_name, search_id)` looks up a process-local `Cancellable`
(`core/scans/cancellable.py`'s `TaskCancellable`/`ProcessCancellable`/`GitCloneCancellable`,
registered per scan under `(feature_name, search_id)` so two features' independently-incrementing
search ids never collide) and awaits its `cancel()` — real cancellation, not just a signal.

## Restart reconciliation

`core/scans/reconciliation.py`'s `mark_stale_running_as_failed` cleans up rows stuck in
`running` state after a process restart interrupted them mid-scan. Each feature's crud module
wraps it as `interrupt_running_searches(db) -> int`; `utils/scan_reconciliation_registry.py` is
the single place that knows every feature's version of that function (mirrors
`router_registry.py`/`scheduler_registry.py`'s "one place knows about every feature" pattern) and
exposes `reconcile_stale_scans()`, called once from `main.py`'s startup lifespan. Adding a new
scan feature to that registry's `_SCAN_FEATURES` list is mandatory, not optional -
`tests/core/test_scan_reconciliation_coverage.py` fails if a crud module defines
`interrupt_running_searches` without being registered, since an unregistered feature's stale
`running` rows are never cleaned up after a restart.

## Frontend: `core/hooks/useResumableScan.js`

Mirrors the backend lifecycle — stream buffering/parsing, backoff reconciliation after a dropped
connection, abort lifecycle. Each feature supplies its own `reduce`/`reconcile` event-to-state
mapping (reading `event.type`/`event.data.*`) and an `api` object; `cancelScan` is exposed
whenever `api.cancelScan` is provided.

A new scan-style feature should use these rather than reimplementing the lifecycle.
