---
title: Username Search
description: Find accounts registered to a username across hundreds of sites.
sidebar:
  order: 50
---

Searches for a username across a large list of sites. Two pluggable, independently selectable
sources back the same result view — pick one per scan:

- **[Maigret](https://github.com/soxoj/maigret)** — runs in-process, with true per-site progress
  streamed live as each site is checked. Configurable timeout, concurrency, and how many
  top-ranked sites to check, plus an optional proxy. Its site database updates independently of
  the app, tracked in settings.
- **[Social Analyzer](https://github.com/qeeqbox/social-analyzer)** — runs as a subprocess of its
  own CLI rather than in-process (its installed package can't be imported directly), so progress
  reporting is coarser: a "started" event, then one terminal result. Configurable timeout and
  top-site count; a hard wall-clock watchdog force-kills a run after 30 minutes even with no
  client still watching, since both settings can be configured unbounded.

Both tools expose their installed version and whether a newer release is available under their
respective settings tabs; installing an update still requires a container rebuild, since both are
pinned in `requirements.txt` at image-build time.

If a username search turns up an Instagram profile, see
[Instagram Search](/corvid/features/instagram-search/) for profile metadata plus follower/followee/post
scans.

## Suggested variants

While you type, the search form suggests other handles the same person might use — separator
changes (`john.smith` / `john_smith`), a dropped or swapped trailing year, first/last-name
patterns (`jsmith`, `smithj`), common nicknames (`john` → `johny`), single-character leetspeak,
and a few prefixes/suffixes. If you paste an email address, its local part is used. Clicking a
suggestion puts it in the box; it doesn't start a scan. Suggestions are generated in the browser
with no lookups, are guesses rather than findings, and a hit under a variant still needs manual
verification — different people share handles.

## Pivot suggestions after a scan

When a scan finishes (also on a past run's detail page), a "Pivot suggestions" block lists:

- **Other usernames and display names** Maigret parsed out of the profile pages it found (linked
  handles, platform IDs, full names). Clicking a handle starts a Maigret search for it. Only
  Maigret-sourced runs carry these, and only for sites whose page it can parse.
- **Handle guesses from each name** (`John Smith` → `johnsmith`, `jsmith`, …), using the same
  rules as the suggested variants above.
- **Possible email addresses** for the searched handle at common providers. Clicking one opens it
  in the [IOC lookup](/corvid/features/ioc-tools/); a separate button opens
  [Email Search](/corvid/features/email-search/) to check which mail providers have the username.

All of it is hypotheses: the same handle or name is often a different person, so verify before
attributing. Nothing here is fetched beyond what the scan already collected.

## Report export

Maigret-sourced scans can export using Maigret's own report writers (see
[Reports & Exports](/corvid/architecture/reports/)). Social-analyzer-sourced scans don't support
export.
