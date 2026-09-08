---
title: Telegram Notifications
description: Get a Telegram message when a scan finishes, a background job fails, a security event happens, or a newsfeed watchlist keyword matches - and optionally run commands from the chat.
---

Corvid can push a Telegram message for scan completions/failures, background job health,
security/instance-management events, and newsfeed watchlist hits — in addition to the in-app
alerts inbox (the bell icon), which every notification goes to regardless of Telegram
configuration.

## Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram and create a bot with `/newbot` to
   get a **bot token**.
2. Message your new bot directly (or add it to a group) so it can message you back, then find
   the **chat ID** to notify — the simplest way is to send the bot a message and check
   `https://api.telegram.org/bot<TOKEN>/getUpdates` for the `chat.id` field.
3. In Corvid, go to **Settings → Telegram**, paste in the bot token and chat ID, and save.
4. Click **Send test message** to confirm delivery before relying on it.
5. Turn on **Enable Telegram notifications**, then choose which events you want pushed.

Like API keys, the bot token is stored encrypted in the database and configured entirely from
the Settings page — no `.env` entry or container restart required.

## What triggers a notification

- **Scans** (Username Search, Email Search, Git Recon, RU Business Check) — a failed scan always
  notifies while Telegram is enabled; a completed or cancelled scan notifies only if "Notify on
  scan completed/cancelled" is on. Turning that toggle off also keeps routine completions out of
  the in-app alerts inbox, not just off Telegram — only failures are guaranteed to show up either
  way.
- **Background jobs** — a notification fires once when a recurring job starts failing, and once
  again when it recovers - not on every failed run, so a job that's been down for a while doesn't
  spam you once per interval.
- **Security & instance management** — the access token being regenerated, an API key being
  added/changed/removed (never the key value itself, only which provider), and a backup export
  or restore succeeding or failing. Also repeated failed access-token attempts against the API,
  rate-limited to at most one notification per 15 minutes so a bot hammering the wrong token
  can't spam you. These always notify while Telegram is enabled, no separate toggle.
- **Newsfeed watchlist matches** — when an incoming article matches one of your keywords under
  **Newsfeed → Settings → Keyword Matching**, only if "Notify on newsfeed keyword matches" is on.
  Turning that toggle off also keeps routine matches out of the in-app alerts inbox, not just off
  Telegram, the same way the scan-completion toggle works.

## Bot commands

Turn on **Enable inbound bot commands** in **Settings → Telegram** to run commands from the
chat itself — off by default, since this lets the bot act on messages you send it rather than
only pushing notifications out:

- `/lookup <value>` — quick IOC lookup across every configured service that supports the
  detected type (IP, domain, hash, email, ...). Replies with a pass/fail line per service; if
  you've also set a **Web base URL** (Settings → Telegram, only needed for this), the reply
  links back to the full per-provider breakdown in the web UI.
- `/digest` — the 10 most recent unread alerts from your in-app alerts inbox.
- `/help` — lists the available commands.

Only messages from the configured **Chat ID** are acted on; anything else is silently ignored.
Corvid checks for new commands by polling Telegram (not a webhook), so no public URL or TLS
certificate is needed — it works the same whether Corvid is reachable from the internet or only
on your local network.
