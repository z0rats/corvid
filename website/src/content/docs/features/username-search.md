---
title: Username Search
description: Find accounts registered to a username across hundreds of sites.
---

Searches for a username across a large list of sites, with live per-site progress. Two
pluggable, independently selectable sources back the same UI:

- **Maigret** — runs in-process with true per-site progress streaming.
- **Social Analyzer** — runs as a subprocess of its own CLI, with coarser (start/finish only)
  progress reporting.

Both tools expose their installed version and whether a newer release is available; installing an
update still requires a container rebuild.
