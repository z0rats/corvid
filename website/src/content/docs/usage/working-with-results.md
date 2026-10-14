---
title: Working with Results
description: Alerts, recent activity, run history, exports, and shareable lookup URLs.
---

## Alerts

The bell in the top bar collects everything Corvid reports in the background: scans finishing or
failing, background jobs that start failing (feed fetching, database refreshes), security events
(the access token regenerated, an API key changed, repeated failed sign-in attempts, backups), and
newsfeed watchlist matches. The badge shows how many are unread; it refreshes every 30 seconds.

Clicking a scan alert opens that run's results. **Mark all read** clears the badge; **Clear**
deletes every alert. Routine "scan finished" and watchlist alerts are only created if enabled under
**Settings → Telegram** — see [Telegram Notifications](/corvid/usage/telegram-notifications/).

## Recent activity

The home screen lists your newest runs across every tool that keeps a history — IOC lookups,
username/email/phone/Reddit/Instagram/Steam searches, Git Recon, Amass, and RU Business Check —
each linking straight to its saved result. Runs of modules you've disabled are hidden.

## Run history

Every history tab can:

- **Filter** the loaded runs by any column value, and **sort** by clicking a column header (click
  again to reverse, a third time to return to newest-first).
- **Load older runs** — the newest 100 are loaded first.
- **Update live** — a run that's still in progress refreshes every few seconds until it finishes.

Deleting a run asks for confirmation first; its saved results can't be recovered.

## Exporting

A run's detail page has **JSON** (the whole saved record) and **CSV** (its main findings table —
found sites, providers, hosts, persons, posts, friends) download buttons. CSV opens cleanly in
Excel, including non-Latin text, and cell values that look like spreadsheet formulas are
neutralized. IOC Lookup, Username Search (Maigret), and RU Business Check additionally offer their
formatted HTML/PDF reports.

## Shareable lookup URLs

IOC Lookup, Sanctions Search, and YouTube keep the current value in the page URL (`?q=...`), so a
reload, the browser's Back/Forward buttons, or a bookmark brings the same lookup back. Revisiting an
IOC lookup within 15 minutes reuses the results already fetched in this browser session instead of
querying every provider again; searching the same value again forces a fresh lookup.
