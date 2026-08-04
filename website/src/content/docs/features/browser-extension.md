---
title: Browser Extension
description: Minimal Chrome extension for sending selected page text straight into IOC lookup.
---

`extension/` is a minimal MV3 Chrome extension ("Corvid Quick Send") — select text on any page,
click the toolbar icon, and it opens a new tab with that text looked up in IOC Tools. No build
step (load unpacked as-is) and no separate auth setup: it just opens `<base_url>/ioc-tools/lookup?q=<selection>`,
and the app handles its own auth from the browser's stored token like any other tab.

## Install

1. Go to `chrome://extensions` and enable **Developer mode**.
2. Click **Load unpacked** and select the repository's `extension/` folder.
3. Click the extension's icon, then **Options** (or right-click the toolbar icon → **Options**)
   to set your Corvid base URL (default `http://localhost:4000`).

## Known limits

This is intentionally the smallest possible slice of a fuller planned extension (context menu,
popup, token-based API calls) — see the "Chrome extension as a thin client" entry in the
project's `ROADMAP.md`. Selection reading is also blocked on `chrome://` pages, the Chrome Web
Store, and a few other restricted origins by Chrome policy, not something the extension can work
around.
