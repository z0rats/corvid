# Steam Recon — architecture and data-source verification

Clean-room reimplementation of the technique described in the SteamReveal README (geolocation
via the social graph, close-friends ranking, CS2 cheater probability). SteamReveal has no
license, so none of its code is reused; this module is built from Steam's public API docs and
the live behaviour recorded below.

## Phase 0 — live verification (2026-09-28)

Probed with plain `curl`, no API key. Anything marked **UNVERIFIED** needs a Steam Web API key
(or Faceit key) and must be re-checked before the corresponding code is written.

### Verified, keyless

| Source | Result |
|---|---|
| `steamcommunity.com/actions/QueryLocations/` | JSON list `{countrycode, hasstates, countryname}`. |
| `.../QueryLocations/<cc>` | JSON list `{countrycode, statecode, statename}` for countries with `hasstates: 1`. For `hasstates: 0` (e.g. `CC`) the body is the literal `null`. Unknown country code → HTTP 400. |
| `.../QueryLocations/<cc>/<state>` | JSON list `{countrycode, statecode, cityid, cityname}`. Confirmed `RU/48` → Moscow `cityid` 41460. Small, stable, cacheable in-process. Send `Accept-Encoding: gzip` handling (httpx does this by default; raw `curl` without `--compressed` printed gzip bytes for one response). |
| `steamcommunity.com/id/<vanity>/?xml=1` | Keyless vanity → `steamID64` fallback. Also exposes `privacyState` (`public`/`friendsonly`/`private`), `vacBanned`, `tradeBanState`, `isLimitedAccount`, `memberSince`, free-text `location`, `realname`, `customURL`. |
| `steamcommunity.com/comment/Profile/render/<id64>/-1/?start=&count=` | Public profile: `{success, total_count, pagesize, comments_html, timelastpost}`; `count` is honoured up to at least 500 (no clamp observed). Private profile: **HTTP 200** with `{"success": false, "error": "This profile is private."}` — status code alone doesn't signal it. |
| Comment HTML selectors | `.commentthread_comment` (one per comment), `.commentthread_author_link` (`href` = profile URL, `data-miniprofile` = 32-bit account id; `steamid64 = 76561197960265728 + accountid`), `.commentthread_comment_text`, `.commentthread_comment_timestamp[data-timestamp]` (epoch seconds). |
| `steamcommunity.com/profiles/<id>/friends/` | 302 to `/id/<vanity>/friends` — HTML scraping route, not used. |
| `api.steampowered.com/...` without a key | HTTP 400 for `GetPlayerSummaries`, `GetFriendList`, `ResolveVanityURL`. `ISteamWebAPIUtil/GetSupportedAPIList` without a key only lists the public `ISteamUserStats` methods. |

### Verified live via the user's own key (2026-09-28)

The user configured their own Steam Web API key under Settings → API Keys and confirmed
`/profile` against a real public profile: `ResolveVanityURL`, `GetPlayerSummaries/v2`,
`GetPlayerBans/v1`, `GetSteamLevel`, `GetOwnedGames` all returned real data end to end
(persona name, level 77, 490 games, self-declared country, no bans) through the deployed app.

### Still not independently verified live

`GetFriendList/v1` (including its documented HTTP 401 for a private friends list, mapped to
`SteamPrivateError`), `GetUserStatsForGame/v2` for CS2 (appid 730, including what a private
"game details" setting returns), and the real 429/`Retry-After` behaviour under quota pressure -
none of these were exercised against the live API during development (no key was available in
the coding session itself, only in the user's separately-running app). `steam_api_client.py`'s
handling of all three is written from Steam's public documentation and defensive coding, not
confirmed against a live response - worth re-checking against a real scan before relying on the
graph/CS2-report code paths in a real investigation.

## Scope decisions

- Steam Web API key required (service key `steam`). No third-party platform-ban (Faceit,
  GamersClub) signal - GamersClub has no public API, and Faceit was explicitly dropped from
  scope.
- No ML service; cheater probability is a transparent weighted-signal logit with per-signal
  explanations and a separate data-coverage indicator. See
  `docs/adr/0015-steam-recon-clean-room-and-heuristic-scoring.md`.
- Ban-watch (scheduled monitoring) is out of scope for the first iteration.
- Friends graph visualisation (self-drawn SVG, capped node count) is in scope.
- English-only UI strings.

## Friends-graph collection and close-friends ranking

`service/steam_graph_service.py`'s `collect_friend_graph`:

1. Fetch the target's own friend list (`GetFriendList`). A private list raises
   `FriendsPrivateError`, surfaced to the scan as `SteamReconError` (an "expected" failure -
   warning-logged, no traceback, same treatment other scan-style features give a bad-input
   failure).
2. Batch-fetch summaries for every friend, keep the public ones (`communityvisibilitystate ==
   3`), sort oldest-`friend_since`-first (an older connection is assumed more likely a
   genuinely close one; a missing `friend_since` sorts last), and cap at `max_friends`
   (`MAX_FRIENDS_DEFAULT` 200, `MAX_FRIENDS_CAP` 500 - `config/steam_recon_config.py`). This cap
   is applied *before* the expensive step below, not after.
3. For each capped candidate, fetch its own friend list (`FRIEND_FETCH_CONCURRENCY` = 8
   concurrent, via an `asyncio.Semaphore`) and compute `mutual_count = |candidate's friends ∩
   target's full friend set|` - the target's *full* friend set, not just the capped candidates,
   so a friend that's mutual with an uncapped/private friend still counts. A candidate whose own
   friends list is private contributes `mutual_count = 0` and is flagged `friends_private`,
   not treated as an error - `friends_analyzed` in the scan record only counts candidates whose
   list was actually fetched.
4. A per-candidate 429 is retried with backoff (honouring `Retry-After` when present, else
   `FRIEND_FETCH_RETRY_BACKOFF_SECONDS * 2^attempt`, up to `FRIEND_FETCH_MAX_RETRIES` = 3)
   rather than failing the whole scan - a scan touching a few hundred friends is expected to
   brush Steam's rate limit occasionally.
5. Candidates are ranked by `mutual_count` descending; the top `CLOSE_FRIENDS_TOP_N` (20) are
   persisted as the scan's close-friends list and shown in the friends graph, but the
   geolocation vote (below) uses every analyzed candidate, not just the top 20.

Bans for every candidate are fetched once (batched) and attached to each `FriendCandidate`, used
both by the close-friends table (VAC/game-ban chips) and the cheater report's
`friend_ban_density` signal.

## Geolocation hypothesis

`service/steam_geolocation_service.py`'s `aggregate_locations` (pure, no I/O - `resolve_
hypothesis_names` does the actual `steam_locations_service` name lookups afterward):

1. "Voters" = every analyzed candidate with `mutual_count > 0` *and* a self-declared
   `country_code`. `coverage` = the fraction of `mutual_count > 0` candidates that have a
   location at all (whether or not they end up a voter for the winning country).
2. Country weight = sum of `mutual_count` across voters sharing that country code; ranked
   descending, top `GEO_TOP_CANDIDATES_PER_LEVEL` (3) kept. State and city weights are computed
   the same way, but *scoped to the leading country/state* - a friend in a losing country never
   contributes to the shown states/cities.
3. Confidence (`GEO_HIGH_CONFIDENCE_SHARE` 0.5 / `GEO_MEDIUM_CONFIDENCE_SHARE` 0.3, each paired
   with a minimum voter count, plus `GEO_MIN_COVERAGE_FOR_MEDIUM` 0.2 for medium) requires the
   leader to have a **strictly greater** vote share than the runner-up - a tied leader (e.g. a
   50/50 split) is never "high confidence" no matter how many voters there are, since it's
   genuinely a coin flip between the two.
4. Only the winning country/state/city get their names resolved (via the keyless
   `QueryLocations` lookup, cached in-process); a close friend's own row in the UI table still
   shows its raw location codes rather than a resolved name, to avoid a name lookup per friend.

## CS2 cheater-probability report

`service/steam_cheater_scoring_service.py`'s `compute_cheater_report` combines five signals into
`probability = sigmoid(LOGIT_BIAS + Σ weight·value)` (`config/cheater_scoring_config.py`,
`LOGIT_BIAS = -3.5` so an all-zero/no-data profile lands near 0.1, not 0.5):

| Signal | Weight | What it measures |
|---|---|---|
| `own_vac_or_game_ban` | 3.0 | Whether the target has a VAC/game ban, scaled by recency (full weight within 180 days, decaying to a 0.3 floor by 3 years) |
| `friend_ban_density` | 2.5 | Mutual-count-weighted fraction of connected friends carrying a VAC/game ban |
| `low_account_investment` | 1.2 | Fraction of {age < 1yr, level < 10, games < 5} thresholds met, among the ones with data |
| `stat_outliers` | 2.0 | Max of headshot-ratio/accuracy/K-D scaled against `STAT_THRESHOLDS`, only scored above `STAT_MIN_ROUNDS_PLAYED` (200) rounds |
| `accusatory_comments` | 1.5 | Fraction of the target's public profile comments (excluding their own) matching `ACCUSATION_LEXICON` (en/ru/pt/de/es substrings), only scored above `MIN_COMMENTS_FOR_SIGNAL` (5) comments |

A signal with no usable data (private stats, too few comments, no candidates) contributes `0` to
the logit and is reported with `value: null`, not scored as innocent - `coverage` on the report
is the fraction of the 5 signals that *did* have data, shown separately so a low probability
built on little data doesn't read the same as one built on a full picture. `already_banned` is
a plain fact check (not part of the heuristic weighting) surfaced alongside the estimate.
Comments are fetched via the same keyless endpoint the phase-0 verification covers above; a
private profile's comment thread (HTTP 200, `success: false`) is treated as "no comments"
rather than an error.

## Known limitations

- Per-candidate location names aren't resolved (only the winning country/state/city are) - the
  close-friends table shows raw ISO/state codes for individual friends.
- The friends graph is a star topology (target ↔ each close friend) - there's no
  friend-to-friend edge, since `collect_friend_graph` never learns whether two *friends* of the
  target are also friends with each other, only how many of the target's friends each one shares.
- Cancelling a scan mid-friends-collection loses the partial graph (the same limitation
  `core/scans/run.py` documents for git_recon) - a bare `asyncio.CancelledError` from the
  `asyncio.gather` over candidate fetches isn't caught and re-packaged with partial results.

## Command-palette integration

`IOC_TYPES.STEAM_PROFILE` (`frontend/src/core/utils/iocTypeDetection.ts`) recognizes a
SteamID64, SteamID3, SteamID2, or a steamcommunity.com profile/vanity URL, pivoting to Steam
Recon's New Scan tab with the value prefilled and the scan auto-started - same mechanism as the
YouTube URL special-case; see `docs/architecture/command-palette.md`. A bare vanity name (no
ID/URL) is deliberately not auto-detected there (too ambiguous against arbitrary free text), so
it still only works typed directly into the New Scan/Profile forms.
