"""YouTube Data API v3 client (https://www.googleapis.com/youtube/v3/{videos,commentThreads}) -
fixed host; unlocks statistics/duration/tags/category/publish date and top-level comments beyond
what oEmbed + page scraping expose. Requires a user-supplied API key under Settings > API Keys
("youtube"). `fetch_video_api_data` is best-effort (any failure is logged and treated as "not
available" rather than failing the whole /lookup, since the keyless tiers already cover the
baseline response); `fetch_comment_threads` raises instead, since comments have no keyless tier
to fall back to - a failure there means the request itself has nothing to return.
"""
import logging
from typing import Any

import httpx

from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
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


async def fetch_comment_threads(
    video_id: str, api_key: str, order: str, page_token: str | None, max_results: int
) -> dict[str, Any]:
    """Fetch one page of top-level comment threads for a video.

    Raises:
        AppHTTPException: On comments-disabled, an invalid/quota-exceeded key, a missing
            video, or a request failure.
    """
    params: dict[str, Any] = {
        "part": "snippet",
        "videoId": video_id,
        "order": order,
        "maxResults": max_results,
        "textFormat": "plainText",
        "key": api_key,
    }
    if page_token:
        params["pageToken"] = page_token

    try:
        async with httpx.AsyncClient(timeout=YOUTUBE_API_TIMEOUT) as client:
            response = await client.get(YOUTUBE_COMMENT_THREADS_URL, params=params)

            if response.status_code == 403:
                if _error_reason(response) == "commentsDisabled":
                    raise AppHTTPException(
                        status_code=403, detail="Comments are disabled for this video",
                        error_code="YOUTUBE_COMMENTS_DISABLED",
                    )
                raise AppHTTPException(
                    status_code=403,
                    detail="YouTube Data API rejected the request (invalid key or quota exceeded)",
                    error_code="YOUTUBE_API_FORBIDDEN",
                )
            if response.status_code == 404:
                raise AppHTTPException(status_code=404, detail="Video not found", error_code="YOUTUBE_VIDEO_NOT_FOUND")

            response.raise_for_status()
            return response.json()

    except AppHTTPException:
        raise
    except httpx.TimeoutException as e:
        logger.error("Timeout fetching YouTube comments for video %s: %s", video_id, e)
        raise AppHTTPException(
            status_code=504, detail="Request timeout while connecting to YouTube", error_code="YOUTUBE_TIMEOUT",
        )
    except httpx.RequestError as e:
        logger.error("Request error fetching YouTube comments for video %s: %s", video_id, e)
        raise AppHTTPException(
            status_code=503, detail=f"Failed to connect to YouTube: {e}", error_code="YOUTUBE_CONNECTION_ERROR",
        )
    except httpx.HTTPStatusError as e:
        logger.error("HTTP status error fetching YouTube comments for video %s: %s", video_id, e.response.status_code)
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"YouTube Data API returned error: {e.response.status_code}",
            error_code="YOUTUBE_API_ERROR",
        )
    except ValueError as e:
        logger.error("Could not parse YouTube comments JSON response for video %s: %s", video_id, e)
        raise AppHTTPException(
            status_code=502, detail="YouTube returned an unexpected (non-JSON) response",
            error_code="YOUTUBE_INVALID_RESPONSE",
        )
    except Exception as e:
        logger.error("Unexpected error fetching YouTube comments for video %s: %s", video_id, e, exc_info=True)
        raise AppHTTPException(
            status_code=500, detail="An unexpected error occurred while fetching YouTube comments",
            error_code="YOUTUBE_UNEXPECTED_ERROR",
        )


def _error_reason(response: httpx.Response) -> str | None:
    """Best-effort extraction of the YouTube API's machine-readable error reason (e.g.
    "commentsDisabled", "quotaExceeded") from an error response body."""
    try:
        errors = response.json().get("error", {}).get("errors", [])
        return errors[0].get("reason") if errors else None
    except Exception:
        return None
