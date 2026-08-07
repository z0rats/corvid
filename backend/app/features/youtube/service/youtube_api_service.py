"""Optional YouTube Data API v3 client (https://www.googleapis.com/youtube/v3/videos) -
fixed host; unlocks statistics/duration/tags/category/publish date beyond what oEmbed +
page scraping expose. Requires a user-supplied API key under Settings > API Keys
("youtube"). Best-effort: any failure (missing/invalid key, quota exceeded, network
error) is logged and treated as "not available" rather than failing the whole lookup,
since the keyless tiers already cover the baseline response.
"""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_API_TIMEOUT = 10.0


async def fetch_video_api_data(video_id: str, api_key: str) -> dict[str, Any] | None:
    """Fetch snippet/contentDetails/statistics/status for a video via the YouTube Data API.

    Returns None if the key is invalid, the video isn't found, or the request fails.
    """
    params = {
        "part": "snippet,contentDetails,statistics,status",
        "id": video_id,
        "key": api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=YOUTUBE_API_TIMEOUT) as client:
            response = await client.get(YOUTUBE_API_URL, params=params)
            if response.status_code != 200:
                logger.warning("YouTube Data API returned status %s for video %s", response.status_code, video_id)
                return None

            data = response.json()
            items = data.get("items") or []
            return items[0] if items else None

    except Exception as e:
        logger.warning("YouTube Data API request failed for video %s: %s", video_id, e)
        return None
