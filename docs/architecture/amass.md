# `backend/app/features/amass/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

Wraps [OWASP Amass](https://github.com/owasp-amass/amass) v5 (`amass` binary, shelled out to)
for active DNS enumeration and ASN/netblock discovery. Why this is a top-level feature with its
own persisted history rather than another stateless `domain_finder` panel, and why the engine
runs as an in-container background process rather than a docker-compose sidecar: see
`docs/adr/0013-amass-engine-in-container.md`.

## Client/engine split

Unlike subfinder/httpx (a single subprocess call each), amass v5's `enum`/`subs` subcommands are
HTTP clients to a separate `amass engine` process that owns the asset graph. `amass_engine_service.py`
starts it once at app boot (`main.py`'s `handle_application_startup`, alongside
`start_bot_polling()`) and `ensure_engine_ready()` is also called defensively before every scan
(idempotent, lock-guarded, self-healing if the engine died between scans) - polling
`ae_isready --host 127.0.0.1` (amass's own readiness-check binary) rather than a raw TCP probe.
No database config means the engine falls back to a local SQLite store under its own
`~/.config/amass/` (`appuser`'s home) - no Postgres, no new docker-compose service.

## Scan shape: two subprocess calls, not one

1. `amass enum -d <domain> -timeout <N>` (`-brute` appended if `ScanRequest.brute_force`) submits
   the domain to the running engine. Its own `-timeout` is an *idle* timeout (minutes without new
   discoveries), not a wall-clock cap, so `amass_service.py` layers a hard
   `WALL_CLOCK_TIMEOUT_SECONDS` ceiling via `asyncio.wait_for` + `core/scans/cancellable.py`'s
   `ProcessCancellable`. `enum`'s own stdout is a raw, `\r`-updated progress bar with no
   structured output - discarded (`DEVNULL`), not parsed.
2. `amass subs -d <domain> -names -ip` reads back everything the engine currently knows about
   that domain as plain `hostname IP` text lines - no `-dir` needed, it reads the same default
   store the engine uses. Called regardless of how step 1 ended (finished, hit the wall-clock
   ceiling, or was cancelled), since whatever was discovered before stopping is still real.

**Findings accumulate in the engine's store across every scan of the same domain** - there is no
per-scan-isolated result set. A repeat scan of `example.com` returns the union of everything
ever discovered for it, not a delta of what changed. `AmassSearch.result` and the frontend's
description text both say this explicitly, so it doesn't read as a bug.

A wall-clock timeout is reported as scan status `cancelled` (with partial results), not `failed`
- see the ADR for why.

## Persistence & lifecycle

First persisted feature in the domain_finder neighborhood (subfinder/httpx/the site crawler are
all stateless). Uses the same `ScanRun` (backend, `core/scans/run.py`) / `useResumableScan`
(frontend) scan-lifecycle pattern as `git_recon` - `AmassSearch` stores its result as a JSON
blob (`{"hosts": [{"hostname", "ip"}, ...]}`), no child table, same shape as `GitReconSearch`
(`docs/adr/0002-git-recon-json-blob-results.md`). `POST /api/amass/scan` streams SSE progress
(coarse-grained: `started` + one terminal event only, amass has no per-host callback to stream);
`.../history` (list/get/delete) and `.../history/{id}/cancel` round out the CRUD.
`crud/amass_crud.py`'s `interrupt_running_searches` is wired into `main.py`'s
`_reconcile_stale_scans`, like every other `ScanRun`-based feature.

## Frontend

Own top-level route (`/amass/new`, `/amass/history`, `/amass/history/:id`) mirroring
`git_recon`'s structure exactly (`state/amassAtoms.js`, `hooks/useAmass.js`,
`services/api/amassApi.js`, `components/{NewScan,ScanForm,ResultsView,HistoryList,HistoryDetail}.jsx`)
- `domain_finder`'s frontend is a single-page panel tool with no routing/history, so a
persisted, cancellable scan couldn't slot in as just another panel there.

## Version/availability

`get_amass_version()` uses `core/utils/cli_tool_version.py`'s shared helper (same as
subfinder/httpx) but with a custom regex - amass's own `-version` output is a bare `vX.Y.Z`,
not projectdiscovery tools' `"Current Version: vX.Y.Z"`.
