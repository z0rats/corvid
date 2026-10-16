---
title: Settings Reference
description: Every settings tab in the app, and what it controls.
sidebar:
  order: 40
---

Global settings live under **Settings** (tabs: General, API Keys, AI Settings, Modules, Command
Palette, Telegram, Backup, About). They're stored in the database (not in `.env`), so they survive
container restarts as long as `data/` is preserved. Newsfeed-specific settings are under
**Newsfeed → Settings** instead, and a few features keep their own settings on the feature page —
see [Newsfeed settings](#newsfeed-settings) and [Per-feature settings](#per-feature-settings).

## General

App-wide preferences:

- **Language** — English or Russian. The Russian translation is incomplete, so some screens stay
  in English.
- **Theme** — light or dark. Also switchable from the sun/moon button in the top bar. Unlike the
  other settings, this one is stored per browser, not in the database.
- **Start screen** — what `/` opens to: the search start screen or the newsfeed.
- **Always use tiles** — render search results as touch-style tiles even when a keyboard is
  present.

## API Keys

Per-service credentials for the integrated OSINT/threat-intel providers (VirusTotal, Shodan,
Hunter.io, GitHub, etc.) — see [External Services](/corvid/architecture/external-services/) for
the full list across every feature. Keys are encrypted at rest before being written to the
database; see [Security → Secrets at rest](/corvid/architecture/security/#secrets-at-rest). Three providers
(VirusTotal, Shodan, Hunter.io) additionally expose a live quota panel here, since those are the
only three whose APIs report remaining quota.

Some entries aren't plain API keys but a stored session or credential for a feature: the Google
account session for Email Search's Google Profile lookup, an imported Instagram browser session,
the Steam Web API key, and the YouTube Data API key.

## AI Settings

Configures which LLM model each AI-assisted feature uses:

- **Default model** — the fallback used by any AI feature with no more specific override.
- Per-feature overrides — newsfeed article analysis, newsfeed report generation, email
  analysis, AI templates, and photo geolocation can each pin a different model, or leave it
  unset to fall back to the default.

Available models come from whichever LLM providers are configured (see
[AI / LLM Providers](/corvid/architecture/ai-providers/)).

## Modules

Enable or disable individual feature modules — a disabled module disappears from the sidebar and
command palette without needing a rebuild or restart. Toggleable modules: Newsfeed, IOC Tools,
Domain Finder, Email Analyzer, Image Tools, AI Templates, CVSS Calculator, Detection Rules,
Dork Runner, Username Search, and Email Search.

## Command Palette

How the search-first palette (`/` or `⌘K`) behaves: whether a single exact match auto-opens.
Playbooks recorded in the palette are listed here too. The start screen and tile options are
under [General](#general). See [Command Palette](/corvid/usage/command-palette/) for the grammar.

## Telegram

Bot token, chat ID, and which events get pushed to Telegram. See
[Telegram Notifications](/corvid/usage/telegram-notifications/) for setup.

## Backup

Download a full backup (database + encryption key, optionally including the access token and
encrypted with a passphrase) or restore one; a restore takes effect after a backend restart. SQLite
only. See [Backup & Operational Security](/corvid/getting-started/backup-and-operations/).

## About

The running version, an "update available" badge when a newer GitHub release exists, and the
**access token** card: show/copy the token this browser uses, forget it (locks this browser), or
**regenerate** it. Regenerating invalidates the old token everywhere immediately, and is disabled
when `API_ACCESS_TOKEN` pins a fixed value in `.env`. See
[Security](/corvid/architecture/security/).

## Newsfeed settings

Under **Newsfeed → Settings**:

- **General** — content retention period and background-fetch interval. Articles older than the
  retention period (default 30 days; **Unlimited** keeps everything) are deleted at the start of
  each fetch, except ones with a note or an AI analysis, and aren't re-fetched while their feed
  still lists them.
- **Manage Feeds** — add/remove/enable feeds, per-feed failure warnings, and an optional
  Admiralty reliability grade (A–F) per feed.
- **Trends** — words and IOC values excluded from the trends charts.

### Keywords

A watch-list of free-text keywords. When enabled, newsfeed articles are scanned
(case-insensitive substring match against title, summary, and full text) and any hits are
recorded per article as `matches`, so you can spot articles relevant to your organization or
interests at a glance without reading every headline.

### CTI Profile

A free-form description of your organization's threat-intelligence profile: profile name, threat
sources you care about, indicators of interest, and a minimum severity threshold. This text is
rendered to Markdown and injected as context into the AI prompts used for newsfeed article
analysis and MITRE ATT&CK enrichment, so the AI's relevance judgment is tailored to your
organization instead of generic.

## Per-feature settings

Some features keep their own settings on the feature page rather than under **Settings**:

- **Username Search** — per-site timeout and how many top sites to check (maigret), plus
  social-analyzer's own options.
- **Email Search** — per-provider timeout, concurrency, proxy/Tor, and the SMTP and headless-browser
  checker groups (both off by default).
- **Phone Search** — per-provider timeout and proxy.
- **RU Business Check** — the thresholds behind the risk flags (fresh registration, claim amounts,
  mass-address, equity ratio, ...) and history retention.

See each feature's page for details.
