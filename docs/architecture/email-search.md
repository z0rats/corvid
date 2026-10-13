# `backend/app/features/email_search/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

Finds which mail providers a username is registered at, via `mailcat-osint`'s ~26 per-provider
checker coroutines (SMTP RCPT probing, provider APIs, registration-form probing, headless
Chromium).

## Execution

Driven in-process — no reusable entrypoint exists in mailcat like maigret's, so
`service/email_search_service.py` runs the checker coroutines itself, bounded by an
`asyncio.Semaphore`. Progress streamed over SSE (`POST /api/email-search/scan`), found-provider
results persisted (`MailSearch`/`MailSearchResult`).

## Checker groups

Two groups are gated off by default via settings (`core/settings/email_search/`,
`enable_smtp_checks`/`enable_headless_checks`):

- **SMTP checkers** (Gmail/Yandex/mail.de) need outbound TCP/25, usually blocked in Docker/cloud.
  Workaround: `use_tor`/`proxy_url`, mirroring mailcat's own `--tor`/`--proxy`.
- **Headless-Chromium checkers** (Fastmail/int.pl/onet.pl, via `requests-html`→`pyppeteer`)
  lazily download a Chromium binary on first real use.

## Timeout and cleanup

Each checker call is wrapped in a hard per-checker `asyncio.wait_for` timeout. mailcat itself
closes its browser handle in a `finally` that survives cancellation, but as a safety net for a
wedged Chromium process that never responds to `browser.close()`, `_kill_orphaned_chromium`
(psutil-based, diffs child PIDs before/after) reaps any Chromium process still alive after a
timeout.

## Versioning

Like social-analyzer (see `docs/architecture/username-search.md`), version/update-check is a
manual PyPI-latest check (`GET /api/email-search/info`, `POST /api/email-search/check-update`),
latest-available version persisted on `EmailSearchConfig`.

## `user_scanner` source

A second source on the same table (`MailSearch.source`: `mailcat` | `user_scanner`, mirroring
`username_search`'s `source`), chosen by `ScanRequest.source`. It takes the **full address** (the
mailcat path strips everything after `@`; `ScanRequest`'s validator is source-aware) and asks each
[user-scanner](https://github.com/kaifcodec/user-scanner) email module whether the service has an
account for it. Why it is a source and not a replacement: `docs/adr/0019-user-scanner-email-source.md`.

- **Execution**: `service/user_scanner_service.py` drives the installed package in-process via
  `user_scanner.core.engine.check` for each module, bounded by the same semaphore/timeout settings
  as mailcat, with the same SSE event shape plus a tri-state `status` (`registered` /
  `not_registered` / `error`). A `Status.ERROR`/`SKIPPED` result is never persisted or reported as
  "not registered". A hit persists as a `MailSearchResult` (`provider_name` = service,
  `emails` = `[address]`, `extra` = `{category, url, fields, links}`); image links in `links` are
  stored but the frontend never renders them.
- **Safety gate (`config/user_scanner_manifest.json`)**: modules run only if the manifest marks
  them `run: true`. The manifest is a reviewed snapshot of every module of the pinned version.
  Blocked: modules on upstream's own "loud" list (they email the owner), plus ones found by
  reading the code that upstream misses (AniList's `ResetPassword` mutation, a Facebook recovery
  flow, two registration/signup POSTs), plus the adult category. A module not in the manifest never
  runs, and `tests/features/email_search/test_user_scanner_config.py` fails until a package
  upgrade's new modules are reviewed. Upstream's own filter is only applied via
  `is_loud(get_site_name(module))`; its list uses display names (`Cv.ee`), not module names.
- **Never imported**: `user_scanner.core.email_orchestrator` monkey-patches `httpx` clients
  process-wide, which would reach our own HTTP clients and the SSRF guard's; only `engine`/
  `helpers` are used, and a test checks `httpx` is left alone. Its settings file is redirected to
  `<data_dir>/user_scanner_config.json` via `USER_SCANNER_CONFIG` (the default is inside the
  installed package).
- **No Tor/proxy**: its modules build their own `httpx`/`curl_cffi` clients and its proxy support is
  a process-global manager, which two concurrent scans would share. A run with `use_tor` or
  `proxy_url` set fails with an explanation instead of sending requests from the host's own IP;
  `/info?source=user_scanner` returns the same text as `blocked_reason` so the UI warns up front.
- **Failed checks**: counted per run in `mail_searches.error_count` (also on the terminal SSE
  event), so history keeps "N checks failed" next to the hits.
- **Missing package**: `GET /api/email-search/info?source=user_scanner` returns `available: false`
  and a run fails with "not installed" rather than breaking startup; the package is imported lazily.
- **Version**: pinned in `requirements.in`, read via `importlib.metadata`; no PyPI "latest" check
  (Dependabot's `pip` updates cover it).
