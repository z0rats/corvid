"""Static config for the YouTube metadata lookup feature."""

THUMBNAIL_VARIANTS = ("default", "mqdefault", "hqdefault", "sddefault", "maxresdefault")

# Plain listing (no query): one page per request, "load more" via page_token.
COMMENTS_LISTING_PAGE_SIZE = 50

# Keyword search: the Data API has no native comment-text search, so this scans multiple
# pages server-side, filtering by author/text substring - capped on both axes so one search
# request can't burn unbounded quota against a heavily-commented video.
COMMENTS_SEARCH_PAGE_SIZE = 100
COMMENTS_SEARCH_MAX_PAGES = 20
COMMENTS_SEARCH_MAX_RESULTS = 50


def build_thumbnail_urls(video_id: str) -> dict[str, str]:
    """Standard YouTube thumbnail URLs for a video ID, by resolution variant.

    Constructed directly with no network call - `maxresdefault` 404s for videos
    never encoded at that resolution, so the frontend should tolerate a broken image.
    """
    return {
        variant: f"https://i.ytimg.com/vi/{video_id}/{variant}.jpg"
        for variant in THUMBNAIL_VARIANTS
    }
