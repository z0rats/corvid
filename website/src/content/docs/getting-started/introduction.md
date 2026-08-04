---
title: Introduction
description: What Corvid is and who it's for.
---

Corvid is a self-hostable, single-user OSINT/security-analyst web app. It replaces a wall of
browser tabs — VirusTotal, Shodan, username-search sites, phishing-domain lookups — with a
single keyboard-first search bar: paste an IP, domain, hash, email, or username and it's routed
to the right tool automatically.

It runs as one Docker Compose stack on your own infrastructure, so investigation data and API
keys never pass through a third-party SaaS. It's a workbench, not a case-management system — fast,
on-demand lookups rather than long-term data warehousing.

:::caution
Corvid is an early prototype and not production-hardened. See the
[disclaimer in the README](https://github.com/z0rats/corvid#disclaimer) before exposing it beyond
a trusted, isolated environment.
:::

## What's next

- [Installation](/corvid/getting-started/installation/) — get Corvid running with Docker Compose.
- [Configuration](/corvid/getting-started/configuration/) — environment variables and settings.
- [Architecture](/corvid/architecture/backend/) — how the backend and frontend are structured.
- [Features](/corvid/features/newsfeed/) — a tour of every module.
