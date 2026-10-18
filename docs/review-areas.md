# Review areas

Checklists for reviewing a change **in a fresh session**, not the one that wrote it: finding a
defect and avoiding one are different tasks for an agent, and a reviewer told which class of bug to
hunt finds what a general "review this" misses. Pick the two or three areas the diff touches; don't
run all of them.

Prompt shape:

> Review `git diff <base>` against the "<area>" and "<area>" sections of `docs/review-areas.md`.
> Report findings only - file:line, the concrete input/state that breaks, and what goes wrong. Don't
> fix anything.

Each item is a question the reviewer answers for every changed hunk in scope. An item earns a place
here only after a bug of that class shipped or nearly shipped - a scar, not a prediction.

## Concurrency and shared state (backend)

- Is a DB row read, then written after an `await`? Another request or scan can change it in between;
  is the write conditional, or is the read-modify-write otherwise atomic?
- Does the change add a writer that can run alongside another one? SQLite takes one writer at a
  time - startup catch-ups (`main.py`'s `_STARTUP_CATCHUPS`) run sequentially for this reason.
- Does in-process state (a module-level cache, `ScanRun.is_queued`, a feed cached for an hour) stay
  correct when two scans or requests touch it at once, and after a restart wipes it?
- A new scheduler job: its interval resets on every restart. Does stale data get caught by a
  startup check that derives staleness from the DB (`is_blacklist_stale`), not just an empty table?
- A new `ScanFeature`: is it in `scan_reconciliation_registry`, so a restart doesn't leave its runs
  `running` forever?

## Concurrency and shared state (frontend)

- Can two requests for the same thing overlap (polling, refocus re-probe, a fast second click)? Is
  only the newest response applied (`useActiveScans`, the LLM model registry)?
- Can a poll or effect re-trigger itself - reopen a menu, refetch in a loop, keep running after
  unmount?
- Does every `fetch()` - including SSE streams outside the shared client - carry the access token?

## Untrusted input reaching the network, filesystem or regex engine

- Does a user-supplied URL or host reach an HTTP client other than `ssrf_guard.safe_get`? A new
  fixed-host client belongs on the reviewed allowlist in `test_ssrf_guard_coverage.py`.
- Does user input reach a subprocess (`git clone`, a CLI tool)? Outside `safe_get`'s reach, so it
  needs its own allowlist (`validate_github_repo_url`).
- Hostnames, regexes and paths built from input: validated before use? Can a pattern backtrack
  catastrophically, or a path escape its directory?

## External source responses

- A parser reads a third-party response: does a renamed or missing field raise `SourceDriftError`,
  or silently read as an empty result (`.get(...) or []`)?
- Is the legitimately-empty answer verified against the real source, not assumed?
- New source: drift and empty test cases (or a reasoned exemption), `ProviderSpec.expects` for
  `ioc_lookup`, and a `Covered`/`Exempt` entry in `tests/canary/coverage_map.py`?

## Secrets and error exposure

- Does exception text reach the client - an HTTP body, an SSE event, a bulk-lookup row? Log it,
  return a fixed message. `httpx` errors embed the request URL, and several providers put the API
  key in it.
- Does a new log line carry a key in a shape `SecretRedactionFilter` doesn't match?
- Does a key or token reach the frontend? Only the Google Maps key does, by decision (ADR 0008).

## Timeouts, cancellation and subprocesses

- A fan-out of tasks (bulk lookups, per-site checks): is there a bound on the *total* time, not just
  per task?
- Cancelling a scan: are child tasks and subprocesses actually stopped, and is the run's final
  state written exactly once?
- A `heavy=True` scan: is every subprocess started inside `run_work`, so it waits for its slot?
- A long subprocess: bounded by a watchdog (`PROCESS_WATCHDOG_SECONDS`)? Is hitting it reported
  with the right outcome for the feature (`amass` reports its timeout as `cancelled`)?

## Data lifecycle

- A setting promises removal (retention, cleanup): does it delete rows, or only hide them?
- A model change: is there an Alembic revision? `main.py`'s `create_all()` bootstraps local dev, so
  a missing migration passes locally and fails only on an upgraded install.

## Dev tooling

- A hook or script that runs `uv` from `backend/`: `backend/pyproject.toml` declares no
  dependencies, so `uv run` resyncs `backend/.venv` to empty. Use the synced venv's own Python.
