"""YouTube oEmbed API client (https://www.youtube.com/oembed) - fixed host, keyless.
Only the video URL query param is user-derived (an already-validated, canonicalized
video ID), never the request host - see ssrf_guard's ALLOWLISTED_FIXED_HOST_FILES.
"""

import logging
from typing import Any

import httpx

from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

OEMBED_URL = "https://www.youtube.com/oembed"
OEMBED_TIMEOUT = 10.0
DEFAULT_HEADERS = {"User-Agent": "Corvid-YouTube-Lookup/1.0", "Accept": "application/json"}


async def fetch_oembed_data(video_url: str) -> dict[str, Any]:
    """Fetch oEmbed metadata (title, author, thumbnail, embed html) for a YouTube video.

    Raises:
        AppHTTPException: When the video is missing/private/embed-disabled, or the request fails.
    """
    try:
        async with httpx.AsyncClient(timeout=OEMBED_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            response = await client.get(OEMBED_URL, params={"url": video_url, "format": "json"})

            if response.status_code in (401, 403, 404):
                logger.info(
                    "YouTube oEmbed reported video unavailable (status %s): %s",
                    response.status_code,
                    video_url,
                )
                raise AppHTTPException(
                    status_code=404,
                    detail="Video not found, private, or embedding disabled",
                    error_code="YOUTUBE_VIDEO_NOT_FOUND",
                )

            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as e:
        logger.error("Timeout fetching YouTube oEmbed data: %s", e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to YouTube",
            error_code="YOUTUBE_TIMEOUT",
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error fetching YouTube oEmbed data: %s", e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to YouTube: {e}",
            error_code="YOUTUBE_CONNECTION_ERROR",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error("HTTP status error from YouTube oEmbed: %s", e.response.status_code)
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"YouTube oEmbed returned error: {e.response.status_code}",
            error_code="YOUTUBE_OEMBED_ERROR",
        ) from e
    except ValueError as e:
        logger.error("Could not parse YouTube oEmbed JSON response: %s", e)
        raise AppHTTPException(
            status_code=502,
            detail="YouTube returned an unexpected (non-JSON) response",
            error_code="YOUTUBE_INVALID_RESPONSE",
        ) from e
    except AppHTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error fetching YouTube oEmbed data: %s", e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching YouTube oEmbed data",
            error_code="YOUTUBE_UNEXPECTED_ERROR",
        ) from e
