---
title: Newsfeed
description: Aggregated cybersecurity news with automatic IOC extraction.
sidebar:
  order: 10
---

Aggregates articles from trusted sources (Wired, The Hacker News, Security Magazine,
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

## Source reliability

Every feed can carry a source-reliability grade on the Admiralty scale used in intelligence work:

| Grade | Meaning |
| --- | --- |
| A | Completely reliable |
| B | Usually reliable |
| C | Fairly reliable |
| D | Not usually reliable |
| E | Unreliable |
| F | Cannot be judged |

Grade a feed from the dropdown in **Settings → Manage Newsfeeds**; the grade then appears as a
badge next to the feed name on each article card (hover it for the wording). `F` means "no basis
to judge", not "worst" — use `E` for a source you know to be unreliable. Feeds you have never
graded show no badge.

**Minimum reliability** in the feed's filters keeps only articles from feeds graded at least that
well (`B` keeps A and B); its choices run from A to E. Feeds you have never graded, and feeds
graded `F`, are hidden while it is set, since neither has a grade to compare. The AI article analysis is also told the feed's grade, so it can weigh the
source.

The built-in feeds start with a grade. Installs that predate grading receive those starting grades
once, on the next start; a grade you set yourself is never overwritten. The starting grades are
only a default, so re-grade any feed to match your own view of it.

Threatpost, which stopped publishing in 2022, is not a built-in feed. An install that already
has it keeps it, ungraded, until you delete it there.
