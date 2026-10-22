# Telegram channel analytics (`features/telegram_search/`)

Deep-dive referenced from AGENTS.md's feature list. Why the keyless web preview and not a user
session: `docs/adr/0029-telegram-channel-analytics-web-preview.md`.

## Flow

`POST /api/telegram-search/scan` (`ScanRequest`: `target`, `max_posts` 1-500, default 100)
validates `target` through `utils/channel_name.py`'s `normalize_channel` (`@x`, `x`, `t.me/x`,
`t.me/s/x`, `t.me/x/123`, `telegram.me/x`, `tg://resolve?domain=x` -> lowercase `x`; invite
links, `t.me/c/...` and reserved paths are a 422) and starts `service/telegram_scan_service.py`'s
`run_scan` as a detached task over SSE. Not heavy: it is a few HTTP requests.

`run_work` emits `progress` with a `stage`:

1. `profile` - `TmeClient.fetch_profile_page` (`t.me/<name>`) -> `tme_parser.parse_profile_page`.
   `None` (the generic "Contact @name" card) fails the run "no public channel or group"; kind
   `user` (the card's extra line is `@name`) fails it as out of scope.
2. `profile_done` (carries `title`, `kind`), then `posts` (`sampled`, `target`) once per preview
   page - `_sample_posts` walks `t.me/s/<name>`, `?before=<cursor>` from each page's
   `<link rel="prev">`, newest first, deduped by post id, stopping at `max_posts`, at the oldest
   page, or when a cursor fails to move back. A redirect on the first page means no preview
   (groups, preview off): the result is the card only.
3. `created` - only when the sample did not reach post #1: one `?before=2` request for the
   "Channel created" service post's date.
4. `analyzing` - `channel_metrics.py` builds the result.

A `CancelledError` while sampling becomes `ScanCancelled` with the partial outcome, so a cancelled
run keeps its posts and metrics.

## Result blob

`TelegramChannelSearch.result` (`schemas.ScanResult`): `profile` (card plus `created_at`,
`preview_available`, preview `media_counters`), `metrics` (None without a preview), `top_posts`
(5 by views), `posts` (every sampled post, newest first, text cut to 500 chars) and `indicators`.
Summary columns for the history list: `channel` (the `target_column`), `title`, `kind`,
`member_count`, `posts_sampled`.

Metrics: posts per day over the sampled date range, average/median/max views, average views /
subscribers, forwarded and media ratios, `top_forward_sources` (linked sources keyed by username,
named-only ones by name, every hidden sender folded into one `name=None` row) and `top_mentions`
(`@name`s and `t.me/<name>` links minus reserved paths like `joinchat`/`addlist`, once per post, excluding the channel itself and the post's own
forward source). Indicators are `ioc_extractor.extract_iocs` over post text, link targets and the
description, minus Telegram hosts (`TELEGRAM_DOMAINS`), capped at 200 per type.

## Parsing and drift

`tme_parser.py` reads BeautifulSoup selectors: `.tgme_page_title`/`.tgme_page_extra`/
`.tgme_page_description` on the card, `.tgme_channel_info` and
`.tgme_widget_message_wrap .tgme_widget_message[data-post]` on the preview. No title and no
"Telegram: Contact @" `og:title`, no channel-info block, a message without `data-post` or with
an unreadable date, and zero matched messages on a page that still has a `rel="prev"` cursor or a
non-empty `.tgme_channel_history` raise `SourceDriftError`; zero messages with neither is a
legitimately empty channel. Counts go through
`parse_count` (`83 253`, `32.1K`, `10.3M`). Fixtures in
`backend/tests/features/telegram_search/fixtures/` are trimmed recordings of real pages, covering
the linked/named/hidden forward shapes and the service post. Live canaries:
`test_keyless_sources_canary.py::test_telegram_profile_card_shape` and
`::test_telegram_channel_preview_shape` (`@durov`).

`TmeClient` (`tme_client.py`) is on the SSRF guard's fixed-host allowlist, sends a browser
User-Agent (Telegram serves a reduced page otherwise), never follows redirects, maps 429 to
`TelegramRateLimitedError` ("retry in N s", `Retry-After` or 60 s) and any other failure to
`TelegramSourceError`, so a failed source fails the run instead of reading as an empty channel.

## Frontend

`frontend/src/features/telegram-search/`: `NewScan` (form, `LiveScanView`, `ChannelReport`) and
history via `useResumableScan`. `ChannelReport` is shared by the live view and the history detail:
overview card (the photo is a link, not an `<img>`, so viewing a report doesn't hit Telegram's
CDN), activity, related channels (a linked forward source or mention opens
`/telegram-search/new?q=<name>`), indicators (domains -> domain finder, hashes -> bulk lookup,
the rest -> IOC lookup) and two post tables.

Command palette: `iocTypeDetection.ts`'s `isTelegramChannelTarget` detects `t.me` links (on top of
the URL match, or as the primary type for a scheme-less link); a bare `@name` reaches the tool
through the identity fallback, where its `telegram` tag ranks it first. `type:telegram` filters
to it.

Not an investigations `RunSource` yet (`run_source_registry.RUN_SOURCE_EXEMPT`).
