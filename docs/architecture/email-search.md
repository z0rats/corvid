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
