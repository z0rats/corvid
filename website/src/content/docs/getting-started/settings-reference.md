---
title: Settings Reference
description: Every settings tab in the app, and what it controls.
sidebar:
  order: 40
---

Settings are reached from the app's **Settings** section and are stored in the database (not in
`.env`), so they survive container restarts as long as `data/` is preserved.

## API Keys

Per-service credentials for the integrated OSINT/threat-intel providers (VirusTotal, Shodan,
Hunter.io, GitHub, etc.) — see [Integrated services](/corvid/features/ioc-tools/) for the full
list. Keys are encrypted at rest before being written to the database; see
[Security → Secrets at rest](/corvid/architecture/security/#secrets-at-rest). Three providers
(VirusTotal, Shodan, Hunter.io) additionally expose a live quota panel here, since those are the
only three whose APIs report remaining quota.

## AI Settings

Configures which LLM model each AI-assisted feature uses:

- **Default model** — the fallback used by any AI feature with no more specific override.
- Per-feature overrides — newsfeed article analysis, newsfeed report generation, email
  analysis, AI templates, and photo geolocation can each pin a different model, or leave it
  unset to fall back to the default.

Available models come from whichever LLM providers are configured (see
[AI / LLM Providers](/corvid/architecture/ai-providers/)).

## General

UI-level preferences: dark/light theme, UI language, and command-palette behavior — whether a
single-match search result auto-opens, which screen the app opens on (`/` route), and whether
results always render as tiles instead of tabs.

## Modules

Enable or disable individual feature modules — a disabled module disappears from the sidebar and
command palette without needing a rebuild or restart.

## Keywords

A watch-list of free-text keywords. When enabled, newsfeed articles are scanned (case-insensitive
substring match against title, summary, and full text) and any hits are recorded per article as
`matches`, so you can spot articles relevant to your organization or interests at a glance
without reading every headline.

## CTI Profile

A free-form description of your organization's threat-intelligence profile — profile name,
threat sources you care about, indicators of interest, and a minimum severity threshold. This
text is rendered to Markdown and injected as context into the AI prompts used for newsfeed
article analysis and MITRE ATT&CK enrichment, so the AI's relevance judgment is tailored to your
organization instead of generic.
