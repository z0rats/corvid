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

## Report export

Maigret-sourced scans can export using Maigret's own report writers (see
[Reports & Exports](/corvid/architecture/reports/)). Social-analyzer-sourced scans don't support
export.
