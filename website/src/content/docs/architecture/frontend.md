---
title: Frontend
description: Frontend stack and layout.
---

## Stack

- **React 19**, **MUI 9**, **Jotai** for state, **react-router-dom 7**
- **Vite** for build/dev server, **Vitest** for tests (jsdom)
- **ESLint 9** flat config, **Yarn 4** (berry)

## Layout

`frontend/src/features/` mirrors the backend feature split — one directory per module
(`newsfeed`, `ioc-tools`, `email-analyzer`, `image-tools`, `llm-templates`, `cvss-calculator`,
`rule-creator`, `username-search`, `email-search`, `reddit-search`, `settings`, ...). Each
feature directory typically has its own `components/`, `hooks/`, `services/`, `constants/`, and
`utils/`. `src/core/` holds shared/cross-feature code.

## Command palette

Corvid is built around a single search bar (`/` or `⌘K`/`Ctrl+K`) instead of menu-hunting: paste a
raw IOC value and it's routed to the right tool, type a tool name to jump to it, or combine both
(`john_doe reddit`) to open a tool pre-filled. See the README's
[Keyboard-first navigation](https://github.com/z0rats/corvid#keyboard-first-navigation) section
for the full grammar.

## i18n

`frontend/src/core/i18n/` holds `en`/`ru` locale files, one JSON per feature namespace. New
features default to English-only.
