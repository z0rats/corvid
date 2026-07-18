"""Shared HTTP fetch helper for dork-runner search engines.

Every engine here queries a fixed, hardcoded host (DuckDuckGo/Google/Bing) -
the dork *query string* is user-supplied, never the host - so this
intentionally does not go through app.core.security.ssrf_guard.safe_get,
which exists for requests to a user-supplied host. See
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES.
"""
import asyncio
import logging
from dataclasses import dataclass

import httpx

from app.features.dork_runner.config.search_engines_config import (
    DEFAULT_HEADERS,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
)

logger = logging.getLogger(__name__)


@dataclass
class RawResult:
    title: str
    url: str
    snippet: str


async def fetch_html(method: str, url: str, *, params: dict | None = None, data: dict | None = None) -> str | None:
    """Fetch a search-engine results page, retrying on transient failures.

    Returns None (rather than raising) once retries are exhausted or the engine
    answers with a non-2xx status, so a blocked/CAPTCHA'd engine degrades to
    "no results for this query" instead of aborting the whole dork run.
    """
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.request(method, url, params=params, data=data)
                if response.status_code == 200:
                    return response.text
                logger.warning(
                    "Dork engine request to %s returned status %s (attempt %s/%s)",
                    url, response.status_code, attempt, MAX_RETRIES,
                )
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(
                    "Dork engine request to %s failed (attempt %s/%s): %s",
                    url, attempt, MAX_RETRIES, e,
                )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

    if last_error:
        logger.warning("Dork engine request to %s exhausted retries: %s", url, last_error)
    return None
