"""Static config for the YouTube metadata lookup feature."""

THUMBNAIL_VARIANTS = ("default", "mqdefault", "hqdefault", "sddefault", "maxresdefault")


def build_thumbnail_urls(video_id: str) -> dict[str, str]:
    """Standard YouTube thumbnail URLs for a video ID, by resolution variant.

    Constructed directly with no network call - `maxresdefault` 404s for videos
    never encoded at that resolution, so the frontend should tolerate a broken image.
    """
    return {variant: f"https://i.ytimg.com/vi/{video_id}/{variant}.jpg" for variant in THUMBNAIL_VARIANTS}
