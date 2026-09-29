# Scan-style feature lifecycle (`core/scans/`)

Deep-dive referenced from AGENTS.md's Conventions section. Shared by every SSE-streamed,
cancellable/resumable, persisted-history feature: `username_search`'s three sources,
`email_search`, `phone_search`, `git_recon`, `ru_business_check`, `amass`, `steam_recon`,
`instagram_search`.

## Declaring a scan feature: `core/scans/feature.py`'s `ScanFeature`

One instance per scan table, in the feature's crud module (`AMASS_SCANS = ScanFeature(name,
model, columns, order_by, relation=None)`). It is the feature's whole lifecycle interface:

- `execute(run_work, on_event, *, create_fields, started_fields, cancellable,
  expected_exceptions, name=None)` - `ScanRun.execute` with the table filled in. `name` is the
  alert/log name; a table written by several sources (username_search) passes its own per run.
- `cancel(search_id)` - by id alone, since ids are unique per table.
- `history` - `make_scan_history_crud`'s list/get/get_with_results/delete.
- `interrupt_running(db)` - restart reconciliation (below).

`core/scans/routes.py`'s `add_run_routes(router, feature, ...)` mounts the four run-history
routes on the feature's router - `POST /{base}/{id}/cancel` (202/404), `GET /{base}`,
`GET /{base}/{id}`, `DELETE /{base}/{id}` - with the feature's schemas, error codes, `base`
(`history` or `runs`), and optional `to_detail`/`after_delete` hooks. The feature keeps only its
own `POST /scan` (request shape, rate limit) and any extra routes (exports, reports). Tested once
in `tests/core/scans/test_scan_feature_routes.py`.

## Running: `core/scans/run.py`'s `ScanRun`

`execute()`:
1. Creates the running row.
2. Emits a `started` `ScanEvent`.
3. Runs the feature's own `run_work(search_id)` coroutine, which emits its own `progress` events
   and returns a `ScanOutcome`.
4. Marks the row completed/cancelled/failed, raises the alert, and emits the matching terminal
   event.

Wire shape is the nested `{"type": ..., "data": {...}}`, adapted onto the raw `asyncio.Queue`
`sse_response` reads from via `core/scans/sse.py`'s `queue_sink`.

## SSE framing (every stream, not just scans)

`core/scans/sse.py`'s `sse_stream(async_iterator)` is the one place the `data: <json>\n\n`
framing and anti-buffering headers live; `sse_response(queue)` is it over a queue, and the
non-scan streams (bulk IOC lookup, newsfeed report analysis) return it over their own async
generators. Client side, `frontend/src/core/services/sseStream.ts`'s `openSseStream` (an
authenticated `fetch` - never `EventSource`, which can't send the bearer token every `/api/*`
route requires) and `readSseEvents` (async generator of parsed frames) are used by
`useResumableScan`, bulk lookup, and the newsfeed report.

## Cancellation

`ScanRun.cancel(model, search_id)` looks up a process-local `Cancellable`
(`core/scans/cancellable.py`'s `TaskCancellable`/`ProcessCancellable`/`GitCloneCancellable`,
registered per run under `(model, search_id)` - two tables' ids can collide, one table's never
do) and awaits its `cancel()` — real cancellation, not just a signal.

## Restart reconciliation

`core/scans/reconciliation.py`'s `mark_stale_running_as_failed` (via
`ScanFeature.interrupt_running`) cleans up rows stuck in `running` after a process restart
interrupted them mid-scan. `utils/scan_reconciliation_registry.py`'s `_SCAN_FEATURES` lists every
`ScanFeature` (mirrors `router_registry.py`/`scheduler_registry.py`'s "one place knows about
every feature" pattern); `reconcile_stale_scans()` runs once from `main.py`'s startup lifespan.
Registering is mandatory - `tests/core/test_scan_reconciliation_coverage.py` imports every
module under `app/features/` declaring a `ScanFeature` and fails on any instance missing from
the list (and on two instances sharing a table).

## Frontend: `core/hooks/useResumableScan.ts`

Mirrors the backend lifecycle and owns the whole transport, derived from
`endpoint: { base, runs }` (the same routes `add_run_routes` mounts): the SSE `POST <base>/scan`
via `fetch` (axios can't stream a body in the browser), stream buffering/parsing, backoff polling
of `GET <base>/<runs>/<id>` after a dropped connection, `POST <base>/<runs>/<id>/cancel`, and the
per-`scopeKey` abort lifecycle. A feature supplies only its `reduce`/`reconcile` event-to-state
mapping (reading `event.type`/`event.data.*`) and passes the request body - already in the API's
snake_case shape - to `startScan`. Tested once in `useResumableScan.test.js` against a faked
network; feature hook tests cover only their `reduce`/`reconcile`. History pages share
`core/components/HistoryTable`/`HistoryDetailHeader`/`ScanStatusChip` (status → chip colour).

A new scan-style feature should use these rather than reimplementing the lifecycle.
