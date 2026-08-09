---
title: Newsfeed
description: Aggregated cybersecurity news with automatic IOC extraction.
sidebar:
  order: 10
---

Aggregates articles from trusted sources (Wired, The Hacker News, Security Magazine, Threatpost,
TechCrunch Security, Dark Reading, and more) so you can stay on top of industry trends and
emerging threats without visiting each site individually.

## What happens to each article

- **IOC extraction** — indicators are pulled out of article text automatically and cross-linked
  into [IOC Tools](/corvid/features/ioc-tools/) for lookup.
- **MITRE ATT&CK mapping** — articles are enriched with relevant ATT&CK techniques.
- **Keyword matching** — if enabled under [Settings → Keywords](/corvid/getting-started/settings-reference/#keywords),
  articles are flagged when they contain a watched keyword.
- **AI analysis and report generation** — optional, using whichever model is configured for
  newsfeed analysis/reports under [AI Settings](/corvid/getting-started/settings-reference/#ai-settings);
  responses are shaped by your [CTI Profile](/corvid/getting-started/settings-reference/#cti-profile)
  if you've filled one in.

## Trends and analytics

Beyond the article feed, the module surfaces trend data over time — useful for spotting a spike
in a particular threat or technique rather than reading article-by-article.

## Feed health

Each configured feed tracks its own last-fetch/last-success/last-error state, updated on every
scheduled run, so a persistently failing feed (bad URL, provider outage) shows a warning in the
feed management UI instead of only ever appearing in logs.
