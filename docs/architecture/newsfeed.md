# `backend/app/features/newsfeed/`

Deep-dive referenced from AGENTS.md's Backend architecture section. RSS aggregation, IOC
extraction from articles, MITRE ATT&CK mapping, trends/analytics.

## Feed health

`process_feed_chunk` sets each feed's `last_fetched_at` / `last_success_at` / `last_error` on every
scheduler run; a failing feed surfaces as a warning in the UI.

## Source reliability

Each feed has a nullable Admiralty `reliability` grade (A-F).
`PATCH /api/settings/modules/newsfeed/{name}/reliability` accepts only A-F, so a grade is never set
back to NULL. Grades are pre-set for `DEFAULT_NEWSFEEDS` and backfilled once by
`create_default_newsfeeds`. Shown as a badge on article cards, filterable via `min_reliability` on
`GET /api/newsfeed/articles` (unrated feeds excluded) and passed to the article-analysis prompt.
