# Reddit Search

Deep-dive referenced from AGENTS.md. User-facing description: `website/src/content/docs/features/reddit-search.md`.

Finds a Reddit user's full post/comment history, including moderator-removed and author-deleted
content, by querying two public archive APIs in parallel - Arctic Shift (`arctic-shift.photon-reddit.com`)
and PullPush (`api.pullpush.io`). No auth or API key; a server-side port of the frontend-only
[Rosint](https://github.com/zuxu4n/Rosint). Both hosts are fixed constants in
`service/reddit_search_service.py` (so they sit on `test_ssrf_guard_coverage.py`'s reviewed
fixed-host allowlist); only the username and paging cursor are user-supplied, and `normalize_username`
reduces a pasted profile URL or `u/name` to the bare handle first.

## Merge and paging

- `fetch_both` calls both archives concurrently (`LIMIT = 100` items each, per-request timeouts in
  `DEFAULT_TIMEOUT`). `_safe_fetch` returns `None` for an archive that errored, so one archive being
  down degrades to the other's results instead of failing the scan.
- `_merge_and_sort` dedupes by Reddit item ID (Arctic Shift wins ties, since it's merged first) and
  sorts descending by `created_utc`. PullPush ignores `over_18` server-side, so NSFW posts are
  filtered client-side when not requested (comments have no `over_18` field).
- `_get_status` (mirroring Rosint's `getStatus()`) classifies an item as moderator-removed
  (`[removed]` text or a `removed_by_category`) or author-deleted (`[deleted]` text or author).
- Pagination is timestamp-cursor-based (`before`/`after`), not offset-based: the archives have no
  stable offset, and new activity would shift one.

## Persistence

One `RedditSearch` row persists per username investigation (`POST /api/reddit-search/scan`, 10/min).
Each page's results are appended idempotently to `RedditSearchResult` (unique on
`search_id` + `kind` + `reddit_id`), so paging back and forth never duplicates rows. History:
`GET /api/reddit-search/history`, `GET .../history/{id}`, `DELETE .../history/{id}`.

This is not a `ScanFeature`: a scan is one request returning one page, not a long-running SSE run,
so it has no cancel/reconciliation lifecycle. There is no settings module.
