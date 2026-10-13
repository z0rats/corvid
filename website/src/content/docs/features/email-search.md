---
title: Email Search
description: Find which mail providers a username is registered at, or which services have an account for an email address.
sidebar:
  order: 60
---

Two sources, picked with the chips above the input. **Mailcat** takes a username; **User Scanner**
takes a full email address (see below).

## Mailcat: a username at mail providers

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

## User Scanner: an email address at online services

Takes a **full email address** and asks about 150 online services (shopping, social, developer,
learning, entertainment, …) whether they have an account for it. A hit is a service that confirmed
the address is registered; where the service's sign-in or signup check also reveals profile
details (a display name, username, user ID, location, account type), they appear under the hit.
Hits are saved to history with the same run lifecycle as Mailcat. It uses
[user-scanner](https://github.com/kaifcodec/user-scanner) (MIT), pinned to an exact version.

This is **active reconnaissance, not a passive lookup**: the address is submitted to every one of
those services from the backend host's own IP.

- **Services that would email the address's owner are skipped.** Some "does this account exist?"
  checks work by starting a password reset or sending a verification code, which lands in the
  target's inbox. Every user-scanner module is reviewed against that and listed in a committed
  manifest; the ones that notify (or that submit a signup form) are blocked, as is the whole adult
  category. A module that appears in a newer version stays off until it has been reviewed.
- **Not combinable with Tor or a proxy.** user-scanner can't be routed through the configured
  proxy, so rather than quietly sending requests from your own IP, a run fails with an explanation
  while Tor or a proxy is set under **Settings → Email Search** (the page warns about this as soon
  as you pick User Scanner).
- **A failed check is not "no account".** Services that block the request, time out or changed
  their API are counted separately ("N checks failed", kept in history too) and never reported as
  "not registered".
- Image links a profile exposes (avatars) are stored but never loaded in the browser.

The installed package version and the number of services that will run are shown above the form.
Updating the package needs a container rebuild, as with the other bundled tools.

## Google Profile (GHunt)

A separate, explicit-click panel on the same page looks up a Google account's public profile
(Google ID, profile/cover photo, last profile edit date, account types, activated services, and
raw Play Games/Maps/Calendar data if any) by email, using
[GHunt](https://github.com/mxrch/GHunt). Nothing runs automatically — the request is made to
Google under your own configured account, so it only fires when you click the lookup button.

**This uses your Google account, not an API.** GHunt needs a real Google account's session
(cookies, OSIDs, an Android master token) — there's no anonymous or API-key mode. Generate one
by running `ghunt login` yourself (locally, with `pip install ghunt` or a temporary venv — this
is a one-time interactive login, not something Corvid can do for you), then paste the resulting
`~/.malfrats/ghunt/creds.m` file's content into **Settings → API Keys → GHunt Session**.

**Use a disposable Google account, never your own daily-driver account.** This kind of lookup is
against Google's Terms of Service, and the account behind the session can get flagged or banned
for it. The session is encrypted at rest, never displayed back once saved, and only ever read
into a throwaway, per-request temporary directory that's deleted immediately after each lookup.

A found `gmail.com`/`googlemail.com` address in a scan's results has a **Google profile** button
that drops it into this panel's email field and scrolls to it; it doesn't run the lookup itself.
(Only on a live scan's results, not the history detail page, which has no lookup panel.)

Only one lookup runs at a time (GHunt's own account gets rate-limited by Google otherwise), and
each is capped at 60 seconds. See `docs/architecture/ghunt.md` in the repository for the full
technical write-up, including what GHunt's raw JSON output actually contains.
