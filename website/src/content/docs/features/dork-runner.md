---
title: Dork Runner
description: Run parameterized search-engine dorks against a domain, username, or email.
sidebar:
  order: 90
---

Runs a library of parameterized dork templates (`site:`, `filetype:`, `intext:`, and more)
against a domain, username, or email — a quick way to surface exposed files, login pages,
paste-site mentions, or other search-engine-indexed content without hand-typing each query.

DuckDuckGo's HTML endpoint is the default search engine, since Google and Bing block scripted
queries almost immediately; Google/Bing remain selectable as best-effort alternatives that may
get rate-limited or blocked. Queries run sequentially with a politeness delay between them, never
in parallel, to reduce the chance of the engine blocking the requests outright.

Results are ephemeral, like Domain Finder — no history is persisted.
