---
title: Email Search
description: Find which mail providers a username is registered at.
---

Checks a username against roughly two dozen mail providers using
[mailcat](https://github.com/sharsil/mailcat)'s per-provider checkers — a mix of SMTP RCPT
probing, provider APIs, registration-form probing, and headless-browser checks — with progress
streamed live as each provider is checked. Found providers are saved to history.

## Checker groups

Two checker groups are off by default, since they need network conditions that aren't available
in every deployment:

- **SMTP checks** (Gmail, Yandex, mail.de) — need outbound TCP/25, which most cloud/Docker
  network setups block. Route around this with `use_tor` or a `proxy_url` in settings.
- **Headless-browser checks** (Fastmail, int.pl, onet.pl) — lazily download a Chromium binary the
  first time any of them runs; see
  [Troubleshooting](/corvid/getting-started/troubleshooting/#email-searchs-headless-browser-checks-are-slow-or-fail-on-first-run).

Enable either group under **Settings → Email Search**.

## Version tracking

Like Username Search, the installed `mailcat-osint` version and whether a newer one is available
are surfaced in settings (a manual PyPI check) — installing an update still requires a container
rebuild.
