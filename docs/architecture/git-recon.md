# `backend/app/features/git_recon/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

Wraps [gitcolombo](https://github.com/Soxoj/gitcolombo) (stdlib-only, imported in-process —
`service/git_recon_service.py` drives its `GitAnalyst` directly rather than calling its CLI
`main()`, so results come back as structured objects instead of parsed ANSI text) to correlate
names/emails/GitHub logins from commit history.

## Modes

`ScanRequest.mode`:
- **`search`** — API-only (GitHub `/gpg_keys` + `/search/commits`), no cloning.
- **`url`/`nickname`** — clone one repo, or every public non-fork repo of a user/org, and
  correlate author/committer identity mismatches across `git log --all`.

## SSE scan lifecycle

`POST /api/git-recon/scan` streams progress over SSE (background `asyncio.create_task` + queue,
same shape as `username_search`/`email_search`), but coarse-grained (`started`/`completed`/
`cancelled`/`failed` only — gitcolombo has no per-item progress callback), so the request doesn't
block for the scan's full duration. Runs can take up to `WALL_CLOCK_TIMEOUT_SECONDS` — nginx's
`/api/` `proxy_read_timeout` is raised to match, or it'd 504 the client mid-scan while the backend
kept running regardless.

Cancellable via `POST /api/git-recon/history/{id}/cancel` and `core/scans/cancellable.py`'s
`GitCloneCancellable`, which reaps the scan's own git subprocesses (psutil, same
before/after-pid-diff pattern as `email_search`'s Chromium reaper — see
`docs/architecture/email-search.md`) rather than cancelling the asyncio task directly, since the
clone/log calls run inside a worker thread (`asyncio.to_thread`) with no cancellation point of
its own.

## SSRF surface

gitcolombo's `git clone` is a `subprocess` call that (unlike every other outbound fetch in this
codebase) isn't `httpx`, so it's outside `ssrf_guard`'s reach. `validate_github_repo_url`/
`validate_github_nickname` in the service module are the sole gate restricting any user-supplied
target to `https://github.com/<owner>/<repo>` before it reaches subprocess argv — regression-tested
in `tests/features/git_recon/test_url_allowlist.py`, since the repo-wide
`test_ssrf_guard_coverage.py` only scans for raw `httpx`/`requests` clients.

Clones into an ephemeral `tempfile.mkdtemp()` dir, `rmtree`'d in a `finally`;
`config/git_recon_config.py` caps repo count/clone workers/wall-clock time per scan (full,
non-shallow clones are needed for `--all` history).

## GitHub PAT reuse

Reuses the `github_pat` row from `core/settings/api_keys` rather than a separate credential —
`nickname` mode's repo-discovery step (`_get_public_repos_count`/`_get_github_repos`) sends it as
a Bearer header itself, since gitcolombo's own equivalents don't accept a token at all (only its
gpg_keys/search-commits calls, used by `search` mode, do) and would otherwise silently fall back
to GitHub's unauthenticated 60/hour cap regardless of a configured PAT.

## `mentions` reconstruction

In `url`/`nickname` mode each identity also carries a `mentions` list (per-repo commit counts +
one sample commit SHA, clickable through to `<repo_url>/commit/<sha>`) — reconstructed in
`_run_clone_mode_sync` by slicing `analyst.commits` per repo right after each `analyst.append()`
call, since gitcolombo's own `Person` only retains a single last-seen repo/commit, not full
provenance.

## Persistence

A `GitReconSearch` row is created in `running` state before the scan starts, updated to
`completed`/`cancelled`/`failed` after (interrupted-by-restart rows reconciled to `failed` by
`main.py`'s `_reconcile_stale_scans`, like the other SSE-scan features). Result stored as a JSON
blob — graph-shaped output, not worth normalizing into FK tables for the only consumer (see
`docs/adr/0002-git-recon-json-blob-results.md`).
