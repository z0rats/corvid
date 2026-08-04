---
title: Command Palette
description: The keyboard-first search bar Corvid is built around.
---

Corvid is built around a single search bar instead of hunting through menus. Press `/` or
`⌘K`/`Ctrl+K` from anywhere to open it.

## Grammar

- **Tool name** — type a tool's name (`reddit`, `git recon`, `whois`) to jump straight to it.
- **Raw value** — paste an IP, domain, email, hash, CVE ID, or crypto address, and Corvid
  suggests which tools can look it up (type is auto-detected).
- **Value + tool pivot** — combine both (`john_doe reddit`) to open that tool with the value
  already filled in and the search triggered. Works for any single-value "identity" lookup:
  Reddit Search, Username Search, Email Search, and Git Recon's nickname mode.
- **`#tag`** — filter by tag, e.g. `#recon`, `#ioc`.
- **`type:kind`** — filter by IOC type, e.g. `type:email`.
- **`>action`** — quick actions, e.g. `>settings`, `>theme`.
- **`defang <value>` / `fang <value>`** — copies a de-fanged/re-fanged IOC straight to the
  clipboard, no need to open a tool for it.
- **Paste an image** (`⌘V`/`Ctrl+V`) — jumps into Image Tools with the image already loaded.

## Playbooks

The palette can record a chain of tools you use together (a "playbook") and replay it later as a
single entry, alongside pinned and recently-used tools. These live in the browser's local
storage, not the server.

## No keyboard handy?

The panel on the left lists every tool, grouped the same way the search tags do — click through
instead of typing. Press `?` any time for the full shortcut list.

## Start screen

The `/` route renders a lighter, non-modal version of the same search grammar by default. Under
**Settings → General**, you can instead have `/` open straight into the newsfeed.
