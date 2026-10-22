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

## Pivots

`GET /api/username-search/runs/{id}` carries `pivots` (`RunPivots`), computed at read time by
`service/pivot_service.py`'s `build_pivots` from the found sites' persisted `extra`
(`discovered_usernames`/`discovered_links`/`discovered_names`/`discovered_emails`, written by
`_build_discovered_extra` at scan time, capped per site). Read-time, so runs saved before a rule
changed pick it up; `discovered_emails` only exists on runs saved after it was added.

- **Link resolution** (`resolve_profile_link`): a short table of well-known platforms goes first,
  because Maigret's site database is a probing database rather than a link resolver - its templates
  miss `x.com`, need `/about` for YouTube, and capture whole paths on greedy `.+?` ones. Everything
  else falls back to the database through a host index with strict checks (no `?`/`*` templates,
  no path-like handles, reserved page names and shorteners rejected). Each table entry's site name
  must exist in the bundled database (test-enforced), since a later single-site check needs
  Maigret's exact name.
- **Kinds**: `reported` (the profile named the account) beats `link` (owner-typed URL) when a
  handle is seen both ways. Non-`username` IDs are `searchable: false`.
- **Emails** only from socid_extractor's own email fields, never free text.

The frontend generates handle guesses itself (`utils/usernameVariants.ts`) and expands the `[...]`
pattern syntax (`utils/usernamePatterns.ts`, bounded to 10,000 matches, 100 shown); neither
touches the backend.

## Following a pivot: site checks, provenance, confidence

`POST /api/username-search/scan/site-check` (body: `username`, 1-5 `site_names`, optional
`parent_search_id`/`pivot_source`) runs Maigret against only the named sites as an ordinary
`maigret` run. It is its own route at `5/minute` because slowapi picks the limit per route and
can't see the body; `/scan` stays `3/minute` and accepts the same two optional fields. Site names
are validated against the loaded database (enabled, `username`-type; canonical casing restored),
unknown -> 422 (the frontend's `openSseStream` shows the response's `detail`).
`get_site_dict(names=...)` ignores `top_sites_count` and drops the mirror sites Maigret's own name
filter drags in. A site check persists every site's verdict in `maigret_searches.site_statuses`
(`claimed`/`available`/`unknown`/`illegal`; NULL for a full scan, which is also how the UI labels
a run as a site check), since only found sites become result rows and a blocked check must stay
"inconclusive" after a reload or in history.

`maigret_searches.parent_search_id` (indexed, deliberately **no FK**: SQLite can't add one by ALTER,
and a deleted parent must not cascade) and `pivot_source` (<= 200 chars, untrusted label) are
exposed on the run summary/detail; readers tolerate a dangling parent. The detail also carries
`parent_exists` (looked up by `_run_detail`, via `add_run_routes`' `to_detail(run, db)`), so the UI
links only to a parent that still exists.

For a run with a parent, `run_scan` rates each found profile at the end (`confidence_service.py`),
writing `extra.confidence` = `confirmed | likely | conflicting | candidate`. Anchors come from the
parent's persisted results: names (order-insensitive, read up to the first comma, handle-echoes
dropped), emails, personal domains (link hosts that are not platforms/shorteners), resolved
(site, handle) pairs, and the parent's own claimed profiles. `confirmed` = the hit's (site, handle)
is a resolved pivot of the parent; `likely` = it echoes a name/email/domain/known account;
`conflicting` = it has a name but none matches (only when the parent has name anchors);
else `candidate`. A parent deleted mid-run leaves hits unrated. On cancellation the partial report
is saved before this parent lookup, so a second cancel arriving during it can't lose the report.

Frontend: the site check has its own state (`site_check` source in `scanAtoms.js`, endpoint
`scanPath: 'scan/site-check'` on `useResumableScan`) so it never collides with a Maigret scan.
History carries a pivot across navigation as `?q=&parent=&site=&src=`
(`crossFeatureNav.PREFILL_CONTEXT_PARAMS`, cleared with `q` by `usePrefillFromQuery`; a param not
listed there is silently dropped). An email `?q=` is the one value that doesn't auto-run: it only
fills the box, and `SearchForm` offers `utils/emailUsernames.ts` candidates (exact, minus `+tag`,
Gmail dotless, separator changes; no per-provider table) as one-click searches.

## Report export

`report_service.py` reuses Maigret's own report writers and only works for maigret-sourced runs;
social-analyzer runs just report `has_export: false`.

## Threat Actor Usernames source

`source="threat_actor_usernames"` (`threat_actor_usernames_service.py`) is a third engine behind the
same unified schema: one `GET https://threatactorusernames.com/api/search?q=<username>` (fixed host,
10 s timeout, no key), persisted like any run. There's no profile URL, so each hit's `site_name` is
the forum, `url_user` is empty, and the matched handle/logo live in `extra`. No per-site progress
(a started event, then one terminal event) and no settings row. The form's source chips are
multi-select, and each selected source starts its own scan; `hudson_rock` (below) is a chip too
but not a `ScanRequest.source`.

## Hudson Rock supplementary check

A keyless, ephemeral check (`GET /api/username-search/hudson-rock`, `hudson_rock_service.py`)
queries Hudson Rock's free infostealer/malware-log-exposure API per username and renders as a
compact clean/found status chip above the found-sites list. Not persisted, not a
`ScanRequest.source` — same pattern as `ioc_lookup`'s newsfeed-mentions cross-reference (see
`docs/architecture/ioc-tools.md`).
