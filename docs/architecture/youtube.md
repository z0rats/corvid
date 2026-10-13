# YouTube

Deep-dive referenced from AGENTS.md. User-facing description: `website/src/content/docs/features/youtube.md`.

Metadata lookup for a YouTube video URL (`POST /api/youtube/lookup`, 30/min) and an optional
comments panel (`POST /api/youtube/comments`, 20/min). Ephemeral like `domain_finder`/`dork_runner`:
no persistence or history.

## Keyless tier

`youtube_lookup_service.py` combines:

- **oEmbed** (`youtube_oembed_service.py`) - title, author, thumbnail, embed HTML. Required: a failure
  here fails the lookup.
- **Page scrape** (`youtube_page_service.py`) - best effort over the watch page's Open Graph /
  schema.org `<meta>` tags for description, duration, publish date, and keywords. It can break when
  YouTube changes markup; when it yields nothing, `page_metadata` is simply `null`.
- **Constructed thumbnail URLs** at every resolution in `youtube_config.THUMBNAIL_VARIANTS`
  (`i.ytimg.com`). `maxresdefault` may 404 for a given video.

## Keyed tier

An optional YouTube Data API v3 key (`core/settings/api_keys`, service key `youtube`; read through
`youtube_api_key_service.py`) unlocks view/like/comment counts, tags, and category
(`youtube_api_service.py`).

Comments (`youtube_comments_lookup_service.py`) are keyed-only - there is no keyless tier:

- With no `query`: a plain paginated listing (`COMMENTS_LISTING_PAGE_SIZE`).
- With a `query`: the Data API has no native comment-text search, so the service pages through
  comments server-side and filters by author/text, bounded by `COMMENTS_SEARCH_MAX_PAGES` and
  `COMMENTS_SEARCH_MAX_RESULTS`. If a cap is hit first the response carries `truncated: true` plus a
  `next_page_token` to continue.
