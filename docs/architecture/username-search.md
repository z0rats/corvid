# `backend/app/features/username_search/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

Two pluggable sources behind one unified schema (`MaigretSearch`/`MaigretSiteResult`, with a
`source` column: `maigret` | `social_analyzer`, and an `extra` JSON column for source-specific
display data), selected per-scan via `ScanRequest.source` (`POST /api/username-search/scan`).

## maigret

Called in-process (not subprocess) via `maigret.checking.maigret()` — true per-site progress
streamed over SSE. Settings under `core/settings/username_search/`: timeout/concurrency/
top-sites-count/proxy, site-database auto-update tracking, plus a manual PyPI-latest-version
check for the `maigret` package itself (`POST /api/username-search/maigret/check-update`).

## social-analyzer

Invoked as a **subprocess** of its installed CLI (`social_analyzer_service.py`, `--output json`),
*not* in-process: the installed package's on-disk module directory is named with a hyphen (not a
valid Python identifier), so it can't be imported — only `importlib.metadata` (version/site-count)
and the console script are usable.

No per-site progress callback exists either, so the SSE stream is coarse (`started` → one terminal
event). Cancellation kills the subprocess, and a `PROCESS_WATCHDOG_SECONDS` (30 min,
`social_analyzer_config.py`) wall-clock ceiling force-kills it even with no client watching, since
`timeout_seconds`/`top_sites_count` can both be user-configured to 0 (unbounded).

Settings/version-check under `core/settings/username_search/social_analyzer_settings_*`
(timeout/top-sites-count, plus a manual PyPI-latest-version check,
`POST /api/username-search/social-analyzer/check-update`).

For both tools, this only flags an available update (`UsernameSearchInfo.update_available`) —
installing it still requires a container rebuild, since packages are pinned in
`requirements.txt` at image-build time, not runtime-installable by the non-root container user.

## Report export

`report_service.py` reuses Maigret's own report writers and only works for maigret-sourced runs;
social-analyzer runs just report `has_export: false`.

## Hudson Rock supplementary check

A keyless, ephemeral check (`GET /api/username-search/hudson-rock`, `hudson_rock_service.py`)
queries Hudson Rock's free infostealer/malware-log-exposure API per username and renders as a
compact clean/found status chip above the found-sites list. Not persisted, not a
`ScanRequest.source` — same pattern as `ioc_lookup`'s newsfeed-mentions cross-reference (see
`docs/architecture/ioc-tools.md`).
