---
title: Frontend
description: Frontend stack and layout.
sidebar:
  order: 20
---

## Stack

- **React 19**, **MUI 9**, **Jotai** for state, **react-router 8**
- **Vite** for build/dev server, **Vitest** for tests (jsdom)
- **ESLint 9** flat config, **Yarn 4** (berry)

## Layout

`frontend/src/features/` mirrors the backend feature split — one directory per module
(`newsfeed`, `ioc-tools`, `email-analyzer`, `image-tools`, `llm-templates`, `cvss-calculator`,
`rule-creator`, `username-search`, `email-search`, `reddit-search`, `settings`, ...). Each
feature directory typically has its own `components/`, `hooks/`, `services/`, `constants/`, and
`utils/`. `src/core/` holds shared/cross-feature code.

## Command palette

Corvid is built around a single search bar (`/` or `⌘K`/`Ctrl+K`) instead of menu-hunting — see
[Command Palette](/corvid/usage/command-palette/) for the full grammar.

## Cross-feature navigation

"Send to X" actions (e.g. an email found in Email Search → IOC Tools, a domain result in IOC
Lookup → Domain Finder) pass the value through a query parameter, and the target feature reads
and clears it on mount. The same mechanism backs the command palette's `value tool` pivot
(`john_doe reddit`) for every "identity" lookup: Reddit Search, Username Search, Email Search,
and Git Recon's nickname mode.

## i18n

`frontend/src/core/i18n/` holds `en`/`ru` locale files, one JSON per feature namespace. New
features default to English-only.
