# Alerts + Telegram notifications

`core/alerts/service/alerts_service.py`'s `raise_alert(db, module, title, message, *,
telegram_category=None)` is the single entrypoint for anything notification-worthy: it
creates an `Alert` row, broadcasts it to connected WebSocket clients (the existing
`core/alerts/` machinery), and, if `telegram_category` is given, best-effort delivers it to
Telegram too. Callers that don't pass `telegram_category` (e.g. the plain `POST /api/alerts`
REST endpoint) just get the DB row + WS broadcast, unchanged from before Telegram existed.
See `docs/adr/0011-telegram-notifications.md` for why this design (reusing `Alert` as the
event bus, no bot-framework dependency) was chosen over a parallel notification system.

## Hook points

Two shared choke points call `raise_alert`, so every current and future feature of that
kind is covered with zero per-feature wiring:

- **`core/scans/run.py`'s `ScanRun.execute()`** — at each of its three terminal branches
  (completed/cancelled/failed), covering all `ScanRun`-based features (`username_search`'s
  three sources, `email_search`, `git_recon`, `ru_business_check`). The message is built
  generically from `feature_name`, `search_id`, `create_fields` (the scan's own identifying
  fields, e.g. `username`), and `outcome.fields`/the exception string — no per-feature
  templates.
- **`core/scheduler.py`'s `wrap_job_errors()`** — covering all 4 recurring jobs
  (`news_fetch`, `maigret_db_refresh`, `blacklist_refresh`, `ru_business_check_retention_sweep`).

Beyond those two shared choke points, individual security/instance-management call sites
raise their own `"security"`-category alerts directly (see below) since there's no single
shared entrypoint for them the way scans/scheduler jobs have: `core/security/routes.py`
(access token regenerated), `core/backup/routers.py` (export/restore success or failure),
and `core/settings/api_keys/routers/api_keys_settings_routes.py` (a key's value added,
changed, or removed — never a bare `is_active`/`bulk_ioc_lookup` toggle, and the message
only ever names the provider, never the key value itself).

A third shape: `features/newsfeed/service/feed_processing_service.py`'s
`store_article_async` raises a `"newsfeed_match"` alert when a newly-stored article matches
one of the user's watchlist keywords (`core/settings/keywords/` — a pre-existing feature;
`store_article_async` already computed `NewsArticle.matches` before Telegram existed, this
just adds a consumer for a non-empty match). Deliberately on its own fresh `managed_session()`
after the article's own session has already committed, not inside the same transaction - a
failure raising the alert must never roll back (and so discard) the article that was already
saved.

## Telegram categories

`TelegramCategory` (`alerts_service.py`) has five values. Two lookup tables
(`_EXISTENCE_TOGGLES`, `_TELEGRAM_ONLY_TOGGLES`) map a category to the `TelegramSettings`
field gating it - absent from both means "always, no dedicated toggle":

- `"scan_failed"` / `"security"` — always creates the alert and pushes to Telegram while the
  master `enabled` switch is on, no dedicated toggle. Both are rare and actionable (a scan
  failure; a security/instance-management event - token regen, API key change, backup
  export/restore, repeated failed-auth attempts).
- `"scan_finished"` (routine completed/cancelled) and `"newsfeed_match"` (watchlist keyword
  hit) are the categories that can fire often and have no other consumer, so their
  `_EXISTENCE_TOGGLES` entry (`notify_scan_events` / `notify_newsfeed_matches`) gates the
  **alert's existence**, not just the Telegram push: if muted, `raise_alert` returns `None`
  without creating anything, to avoid flooding the in-app alerts inbox for anyone who hasn't
  opted in.
- `"job_transition"` — always creates the alert (edge-triggered, see below, so inherently
  rare); its `_TELEGRAM_ONLY_TOGGLES` entry (`notify_job_failures`) gates only the Telegram push.

### Failure-path alerts need a fresh session, not the request's

A `raise_alert` call inside a route's `except` block (e.g. backup export/restore failure)
must not reuse that request's `SessionDep` — `core/dependencies.py`'s `get_db()` rolls back
the whole transaction once the exception propagates past it, which would silently discard
the just-created `Alert` row (the WS broadcast/Telegram push already happened for real by
then and are unaffected, since those aren't part of the DB transaction). Open a fresh
`managed_session()` for these instead, same as `ScanRun`/`wrap_job_errors` already do.

### Rate-limiting a hot, adversarial path: failed auth attempts

`core/security/access_control.py`'s `verify_access_token` runs on nearly every request, so a
bot or stale client hammering it with a bad token could otherwise trigger one alert (and one
Telegram POST, up to its 10s timeout) per rejected request — a self-inflicted slow-response
DoS if awaited inline. `_record_failed_auth()` instead rate-limits to at most one alert per
15-minute window (`_FAILED_AUTH_ALERT_COOLDOWN_SECONDS`, module-level `_failed_auth_count`/
`_last_failed_auth_alert_at`), naming how many attempts were rejected in that window, and
fires it via `_fire_and_forget` (`asyncio.create_task` + the standard done-callback pattern
to prevent GC, not FastAPI's `BackgroundTasks` — a dependency that raises before a response
is built can't reliably attach one) so a rejected request's own latency is never affected.

## Edge-triggered job failure notifications

`wrap_job_errors` tracks a process-local `dict[str, bool]` (`_job_failing`, module-level in
`core/scheduler.py`) keyed by `job_name`. A failure only raises an alert on the
healthy→failing transition (first failure after a success, or the very first run); it raises
a second "recovered" alert on failing→healthy. A job that stays down for days therefore
produces exactly one failure alert, not one per scheduler tick. Like `ScanRun`'s own
`_registry`, this state resets on process restart — worst case after a restart is one
duplicate notification, never silence.

## Delivery

`core/settings/telegram/service/telegram_client.py`'s `send_telegram_message(bot_token,
chat_id, text)` POSTs to `https://api.telegram.org/bot{token}/sendMessage`. Fixed vendor
host, so it's on `test_ssrf_guard_coverage.py`'s `ALLOWLISTED_FIXED_HOST_FILES` rather than
going through `ssrf_guard.safe_get`. It raises `TelegramDeliveryError` on any failure, built
only from the HTTP status code / exception class name — never the underlying httpx
exception's `str()`/`repr()`, which would embed the bot token (it's a URL path segment, not a
header or query param) into logs. `alerts_service.raise_alert` catches and logs (`warning`,
never raises) this error; the settings page's `POST /api/settings/telegram/test` endpoint
(`telegram_settings_service.send_test_message`) is the one caller that lets it surface, since
that endpoint exists specifically to validate configuration.

## Settings

`core/settings/telegram/` follows the same singleton-settings pattern as `ai_settings`/
`general` (`core/settings/singleton.py`'s `get_or_create_singleton` +
`settings_router_factory.py`'s `build_singleton_settings_router`): one row, `bot_token`
encrypted at rest via the shared `EncryptedString` `TypeDecorator` (now in
`core/security/secrets_crypto.py`, alongside `api_keys`'s use of the same type). Unlike
`api_keys`, the settings response returns `bot_token` in plaintext to the frontend — matching
this app's existing convention for `ApikeySchema.key` (single-user, access-token-gated app,
no masking anywhere else).

## Inbound bot commands

`core/telegram_bot/` is the other direction: commands typed into the Telegram chat that
Corvid acts on. Deliberately deferred by ADR 0011 pending a webhook-vs-polling decision;
ADR 0012 (`docs/adr/0012-telegram-bot-polling.md`) makes that call (long-polling, since the
default deployment has no public HTTPS endpoint) and covers the rest of the design
reasoning (no bot-framework dependency, non-conversational command handling, sequential
processing within the loop).

`service/polling_service.py`'s `_poll_loop` runs for the life of the process (started from
`main.py`'s lifespan via `start_bot_polling()`, stopped via `stop_bot_polling()` — the first
persistent, gracefully-stoppable background task in this codebase; contrast with the two
fire-and-forget, run-once `asyncio.create_task(...)` calls already in `main.py`'s startup).
Each iteration re-reads `TelegramSettings` fresh and idles (30s sleep) unless
`is_usable() and bot_commands_enabled` are both true — this sidesteps needing a
settings-changed hook to start/stop the loop; a config change takes effect on the next
iteration (worst case one 25s long-poll timeout's delay). `deleteWebhook` is called once
per bot-token change (`getUpdates` and a webhook are mutually exclusive in the Bot API).

`service/command_dispatcher.py`'s `_handle_update` is the security boundary: it silently
drops (no reply) any update whose `message.chat.id` doesn't match the configured
`chat_id` — without this check, anyone who found the bot on Telegram could run lookups (and
read alert titles) through this Corvid instance. It then parses the first whitespace-token
as the command (stripping a `@BotName` suffix Telegram appends in groups) and dispatches to
`service/commands.py`'s three handlers, each returning plain reply text:

- `handle_help()` — static command list.
- `handle_digest(db)` — the 10 most recent unread alerts via `alerts_crud.get_unread_alerts`,
  one `[module] title` line each.
- `handle_lookup(db, value)` — reuses existing single-lookup machinery rather than
  reinventing fan-out: `determine_ioc_type` for classification,
  `ioc_lookup_engine.get_all_service_configs` to find configured services supporting that
  type, then `asyncio.gather` over `bulk_ioc_lookup_service.run_single_lookup_with_rate_limit`
  (the same function bulk lookup uses) per service. The reply is a condensed pass/fail line
  per service, not a merged verdict — `LookupResult.data` is an opaque, provider-specific
  dict with no common malicious/score field across providers, so cross-provider verdict
  aggregation is a real but unattempted future extension. An immediate "Looking up..." ack
  is sent before the gather (which can take tens of seconds per the retry/backoff config in
  `rate_limiting_config.py`). If `TelegramSettings.web_base_url` is set, the reply also links
  `{web_base_url}/ioc-tools/lookup?q={value}` for the full per-provider breakdown in the web
  UI — the same `?q=` pivot the command palette already uses.

`bot_commands_enabled` defaults to `False` (unlike the outbound notification toggles, which
default on) since inbound commands are a different trust boundary — the bot now acts on
messages, even though the `chat_id` check gates it.
