---
title: YouTube
description: Look up metadata for a YouTube video URL.
---

Looks up metadata for a YouTube video from a pasted URL (`youtube.com/watch`, `youtu.be`,
`/shorts`, `/embed`, or `/live` links all work) — title, author/channel, description, duration,
publish date, keywords, and thumbnails at every standard resolution.

Two tiers of data are available:

- **Keyless** — always available, no setup required. Combines YouTube's public oEmbed endpoint
  (title, author, thumbnail, embed HTML) with a best-effort scrape of the video page's Open
  Graph/schema.org tags for fields oEmbed doesn't expose (description, duration, publish date,
  keywords). Thumbnail URLs at every standard resolution are constructed directly, no extra
  request needed — higher resolutions (e.g. `maxresdefault`) may not exist for every video.
- **Extended stats** — needs a free YouTube Data API v3 key (`console.cloud.google.com`),
  configured under Settings → API Keys like any other provider. Unlocks view/like/comment counts,
  tags, and category, on top of the keyless data above.

That same API key also unlocks the **comments panel** — there's no keyless tier for comments.
Load top comments (newest-first or top-first) with pagination, or search: YouTube's API has no
native comment-text search, so a search scans multiple pages server-side, filtering by author or
text. A heavily-commented video's search stops after a page/result cap rather than scanning
forever — a "load more" button continues the scan from where it left off.

Results are ephemeral, like Domain Finder and Dork Runner — no history is persisted. Pasting a
YouTube link into the command palette (`/` or `⌘K`/`Ctrl+K`) suggests this module directly.
