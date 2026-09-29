# Instagram Search

Looks up a public Instagram profile's metadata by username via
[Instaloader](https://github.com/instaloader/instaloader) (MIT license). Two phases, both
implemented: Phase 1 is a single profile-metadata lookup, ephemeral like `youtube`/`dork_runner`
(no persistence/history); Phase 2 is a followers/followees/posts scan, persisted via `core/scans`
(SSE-streamed, cancellable, history-backed) - see its own section below.

## Shared plumbing (`service/instagram_common.py`)

Both phases build their `Instaloader` instance via `build_loader()` and map its exceptions via
`raise_mapped_instaloader_exception(exc, username)` - one place, so the two don't drift on how a
given failure is classified. `build_loader()` sets every download/write flag off (nothing touches
disk, no media fetched, only JSON) and `iphone_support=False` (see "Findings" below).

## Phase 1 - profile lookup

`POST /api/instagram-search/profile` → `instagram_search_service.perform_profile_lookup()`:

1. Reads the optional configured session via `instagram_session_service.get_session_dict()`.
2. Runs the actual Instaloader call in a worker thread (`asyncio.to_thread`) — the library is
   synchronous (`requests`-based) and cannot be cancelled once started.
3. If a session is configured, calls `context.load_session(<placeholder>, session_dict)` before
   `Profile.from_username(context, username)`.
4. Reads every needed `Profile` field **inside the worker thread**, before returning to the event
   loop — see "Findings" for why.

## Phase 2 - followers/followees/posts scan

`POST /api/instagram-search/scan` → `instagram_scan_service.run_scan_task()`, driven by
`core/scans/run.py`'s `ScanRun` (the same SSE-started/completed/cancelled/failed lifecycle as
`git_recon`/`amass`/`steam_recon`), persisted to the `instagram_searches` table
(`InstagramSearch` - a JSON-blob `result` column, no child table, same shape as
`GitReconSearch`).

- **`followers`/`followees` need a configured session.** `Profile.get_followers()`/
  `get_followees()` raise `LoginRequiredException` immediately if the context isn't logged in,
  regardless of the target profile's own privacy setting - unlike Phase 1's lookup, there's no
  anonymous tier for either. `posts` works in both modes.
- **The whole scan runs inside one `asyncio.to_thread` worker** (`_scan_sync`), iterating
  Instaloader's `NodeIterator` (a blocking generator backed by `requests`) one item at a time.
  There's no subprocess or asyncio-level cancellation point to hook into, so cancellation is
  cooperative: `core/scans/cancellable.py`'s new `CooperativeCancellable` wraps a
  `threading.Event` that `cancel()` sets and `_scan_sync`'s loop polls itself between items,
  alongside a wall-clock deadline checked the same way (an `asyncio.wait_for` around the thread
  would abandon *waiting* on it without actually stopping it, since a thread blocked in a
  `requests` call can't be forcibly torn down). `SCAN_MAX_ITEMS` (200) is a third, independent
  stop condition on top of those two - whichever is hit first, the scan reports `truncated: true`
  with whatever it collected.
- **Only cheap fields are captured per item**, to avoid a hidden per-item network call:
  `followers`/`followees` items carry just `username`/`full_name`, both read straight off the
  edge-list node Instagram already returned for the whole page (`Profile._metadata()` only makes
  an extra request on a cache miss, and these two fields are always present there); `posts`
  items carry `shortcode`/permalink/date/`is_video`/likes/comments/a caption truncated to 500
  chars. Nothing resembling `profile_pic_url`/`Post.url` (Phase 1's per-profile equivalent) is
  read for scan items.
- Reuses Phase 1's `raise_mapped_instaloader_exception` for a scan failure's message, but every
  outcome still lands as the scan's generic `failed` status - Phase 2 doesn't re-expose the
  mapped HTTP status code anywhere, since there's no synchronous response to attach it to.

## Session storage

Reuses the existing encrypted `Apikey` row (`core/settings/api_keys`, service key
`instagram_session`) rather than a new table — the column is already `Text`-sized and already
encrypted at rest. The value is a JSON object of cookies (`{"sessionid": "...", "csrftoken": "...",
"ds_user_id": "..."}`), imported from a logged-in browser session — **never a password**: password
login risks a checkpoint/2FA challenge and is a faster route to an account ban. Validation
(`instagram_session_service.get_session_dict()`) happens at *use* time, not at save time — the
generic `Apikey` create/update endpoints have no per-service validation hook, and adding one just
for this single case would be more invasive than validating on read. A malformed/incomplete stored
session (bad JSON, not a dict, missing a required key) logs a warning (never the value) and the
lookup silently falls back to anonymous mode, rather than failing the request outright.

## Findings (from reading the installed Instaloader's source, verified 2026-09-28, v4.15.3)

- **File-session methods are `pickle`-based.** `InstaloaderContext.load_session_from_file`/
  `save_session_to_file` deserialize with `pickle.load` — loading one from untrusted content is
  arbitrary code execution. This feature uses only the dict-based
  `load_session(username, sessiondata)` / `save_session()` API. A structural test
  (`tests/features/instagram_search/test_no_pickle_session_methods.py`, same style as
  `test_ssrf_guard_coverage.py`) fails the build if either banned method name appears anywhere in
  `app/`.
- **Minimum viable session cookie set**: `sessionid`, `csrftoken`, `ds_user_id`.
  `InstaloaderContext.load_session` reads `cookies['csrftoken']` directly to set the
  `X-CSRFToken` header and raises a bare `KeyError` if it's absent; `sessionid`/`ds_user_id` are
  what actually authenticate the session with Instagram — without them it behaves like an
  anonymous one. `load_session`'s `username` argument is only recorded locally
  (`context.username = username`), never sent to Instagram or checked against the cookies, so a
  fixed placeholder (`SESSION_OWNER_PLACEHOLDER`) is used instead of tracking the real one.
- **`Profile.from_username` only ever raises `ProfileNotExistsException`** — it resolves through
  `api/v1/users/web_profile_info/`, which returns the full profile node (bio, counters, privacy
  flag) for a private, unfollowed profile too. So "private profile without a following session →
  return the available metadata with `is_private: true`, not an error" falls out of the library's
  own behavior for Phase 1; no special-casing needed. `PrivateProfileNotFollowedException` is
  still mapped defensively (`401 INSTAGRAM_SESSION_REQUIRED`) since a future Instaloader version
  or a Phase 2 call path (`get_posts()`/`get_followers()`) could raise it.
- **`Profile.profile_pic_url` can trigger its own blocking network call** when `iphone_support`
  is on (the default) and the context is logged in — it lazily fetches an iPhone-app-shaped
  endpoint for the HD URL. Reading it from the caller's side of `asyncio.to_thread`, after the
  thread returns, would silently run that request on the event loop. Every `Profile` field this
  feature needs is read inside `_fetch_profile_sync` (still on the worker thread) for exactly
  this reason, and `iphone_support=False` avoids the extra call outright — Phase 1 only needs
  the lower-quality URL anyway (link-only, see below).
- **Exceptions actually reachable by this code path**: `ProfileNotExistsException` (404),
  `LoginRequiredException`/`PrivateProfileNotFollowedException` (401), `TooManyRequestsException`
  (429 — must be caught before `ConnectionException`, since it's a subclass of it),
  `ConnectionException` (503), `BadResponseException`/`QueryReturnedBadRequestException`/
  `QueryReturnedForbiddenException` (502), with a final `InstaloaderException` catch-all (502) for
  anything else. `LoginException`/`TwoFactorAuthRequiredException`/`BadCredentialsException` are
  **not** mapped — they're only raised from `context.login()`/`two_factor_login()`, which this
  feature never calls (no password auth, per the design decision above), so they're unreachable
  dead code here.
- Anonymous requests are rate-limited by Instagram aggressively and unpredictably — this is
  expected, not a bug; the API layer's `429`/`503` mapping is what surfaces it cleanly instead of
  a raw exception.

## Profile picture

Shown as a link only, never embedded (`<img src=...>`), in both modes. Embedding it would leak
the analyst's IP to Instagram's CDN and would need an `img-src` exception in the SPA's strict CSP
(`frontend/nginx.conf`). A server-side proxy through `safe_get` was considered and deferred —
open question below.

## SSRF

Instaloader's `requests` client only ever talks to Instagram's own fixed hosts; there's no
user-supplied URL for `app.core.security.ssrf_guard.safe_get` to validate, so this feature isn't
on `test_ssrf_guard_coverage.py`'s allowlist (that test only scans `app/` for raw
httpx/requests/aiohttp client construction — Instaloader's own client lives in the dependency,
outside its scan root).

## Open questions (deferred)

- Settings UI: the session's JSON value fits the existing single-line API-key field's 500-char
  limit for the minimal 3-key set, but a textarea input would be friendlier for a user who pastes
  a larger cookie export (same open question as GHunt's session import).
- Profile picture: server-side proxy through `safe_get` (with a `*.cdninstagram.com`/`*.fbcdn.net`
  allowlist) instead of a bare link, if analyst-IP exposure to Instagram's CDN turns out to matter
  in practice.
