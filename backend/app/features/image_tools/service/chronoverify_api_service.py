"""ChronoVerify API client (https://chronoverify.com/docs) - reads EXIF/XMP capture
metadata, validates C2PA Content Credentials against the official trust list, and
runs pixel-forensic manipulation checks on an uploaded image.

The verify endpoint works keyless (free, rate-limited per IP) or with an optional
Bearer key configured under Settings > API Keys for higher/production limits - see
chronoverify_service.py for which one gets used. Fixed host, no user-supplied URL
involved, so this is exempt from ssrf_guard (see test_ssrf_guard_coverage.py).
"""

import logging

import httpx

logger = logging.getLogger(__name__)

CHRONOVERIFY_VERIFY_URL = "https://chronoverify.com/v1/verify"
CHRONOVERIFY_TIMEOUT = 30.0


async def fetch_chronoverify_verdict(filename: str, data: bytes, api_key: str | None) -> dict:
    """Submit image bytes to ChronoVerify and return the raw verdict JSON.

    Raises:
        ValueError: for a client-actionable failure (unsupported format, oversized
            file, or a rate limit) with a message safe to show the user as-is.
        httpx.HTTPError: for anything else (timeout, connection error, 5xx) - left
            to the caller/run_file_endpoint to fold into a generic failure.
    """
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    files = {"file": (filename, data)}

    async with httpx.AsyncClient(timeout=CHRONOVERIFY_TIMEOUT, headers=headers) as client:
        response = await client.post(CHRONOVERIFY_VERIFY_URL, files=files)

    if response.status_code == 413:
        raise ValueError("Image exceeds ChronoVerify's 40-megapixel / 25MB limit")
    if response.status_code == 415:
        raise ValueError("ChronoVerify does not support this image format")
    if response.status_code == 429:
        raise ValueError("ChronoVerify rate limit reached - try again shortly, or add an API key")
    if response.status_code == 401:
        raise ValueError("ChronoVerify rejected the configured API key")

    response.raise_for_status()
    return response.json()
