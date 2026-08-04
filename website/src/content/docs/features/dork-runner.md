---
title: Dork Runner
description: Run parameterized search-engine dorks against a domain, username, or email.
---

Runs a library of parameterized dork templates (`site:`, `filetype:`, `intext:`, and more)
against a domain, username, or email. DuckDuckGo's HTML endpoint is the default engine, since
Google and Bing block scripted queries almost immediately; Google/Bing remain selectable as
best-effort alternatives. Queries run sequentially with a politeness delay between them, never in
parallel. Results are ephemeral — no history is persisted.
