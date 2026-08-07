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

Results are ephemeral, like Domain Finder and Dork Runner — no history is persisted. Pasting a
YouTube link into the command palette (`/` or `⌘K`/`Ctrl+K`) suggests this module directly.
