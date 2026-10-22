---
title: Telegram Channels
description: Profile a public Telegram channel or group - subscribers, activity, reposted sources, mentioned channels and indicators - without a Telegram account.
sidebar:
  order: 175
---

Profiles a public Telegram channel or group from Telegram's own public web pages: no Telegram
account, no API key and no session. Enter a username in any of these forms:

- `@durov` or `durov`
- `https://t.me/durov`, `https://t.me/s/durov`, or a post link like `https://t.me/durov/531`
- `telegram.me/durov` or `tg://resolve?domain=durov`

Private invite links (`t.me/+...`, `t.me/joinchat/...`, `t.me/c/...`) are rejected, since the
chats behind them are not public.

## What a scan returns

- **Card**: title, verified badge, description, exact subscriber (channel) or member and
  online (group) count, a link to the profile photo, and the preview's photo/video/file/link
  totals.
- **Created**: the date of the channel's first post, the "Channel created" message.
- **Activity**, over the sampled posts: last post, posts per day, average and median views,
  average views per subscriber, share of forwarded posts and of posts with media.
- **Related channels**: the sources the channel reposts most, and the channels it mentions most
  (`@name` or a `t.me` link). Click a public one to analyze it in turn. A forward from a private
  channel shows its name only; a sender who hides forward attribution is counted as "Hidden
  sender".
- **Indicators**: domains, URLs, IPs, emails, CVEs and hashes found in the sampled posts and the
  description, with Telegram's own links left out. Click one to send it to IOC Lookup (domains go
  to Domain Finder, hashes to Bulk Lookup).
- **Posts**: the five most viewed and every sampled post, newest first, with date, views, forward
  source and the start of its text.

The **Posts to sample** slider (20-500, default 100) sets how many of the newest posts are read.
Telegram shows about 20 posts per page, so 100 posts is about 7 requests to `t.me`, spaced half a
second apart. A running scan can be cancelled and keeps what it has read; past scans are under the
**History** tab and can be exported as JSON or CSV.

## Limits

- **Groups** and channels whose owner turned the **web preview off** return the card only: Telegram
  shows their messages to logged-in users only.
- **User and bot accounts** are out of scope; the scan says so instead of returning a result.
- **View counts** are rounded by Telegram (`32.1K`), so view averages are approximate.
- Telegram can rate-limit a burst of scans; the scan then fails with "retry in N s".
- Sampling reads the newest posts only. Raise the slider for a longer window.

Pasting a `t.me` link into the command palette (`/` or `⌘K`/`Ctrl+K`) offers this tool first; an
`@name` lists it first among the identity tools; `type:telegram` filters to it.
