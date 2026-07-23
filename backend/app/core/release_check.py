import logging
import time

import httpx

logger = logging.getLogger(__name__)

GITHUB_RELEASES_URL = "https://api.github.com/repos/z0rats/corvid/releases/latest"
SUCCESS_CACHE_TTL_SECONDS = 3600
FAILURE_CACHE_TTL_SECONDS = 300
REQUEST_TIMEOUT = httpx.Timeout(5.0)

_cached_version: str | None = None
_cached_at: float = 0.0
_cache_ttl: float = FAILURE_CACHE_TTL_SECONDS


async def _fetch_latest_tag() -> str:
    """Fetch the latest release tag_name from the GitHub API (e.g. 'v2.0.3')"""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            GITHUB_RELEASES_URL,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        return response.json()["tag_name"]


async def get_latest_release_version() -> str | None:
    """Return the latest published GitHub release version (without the leading 'v').

    Cached in memory so the About page doesn't hit GitHub's API on every view:
    SUCCESS_CACHE_TTL_SECONDS after a successful lookup, but only
    FAILURE_CACHE_TTL_SECONDS after a failed one (offline/air-gapped deployment,
    GitHub unreachable or rate-limited) so a transient outage doesn't black out
    the feature for a full hour. Failures are logged and swallowed - the last
    known-good version (or None if there isn't one yet) is returned instead.
    """
    global _cached_version, _cached_at, _cache_ttl

    if _cached_at and (time.monotonic() - _cached_at) < _cache_ttl:
        return _cached_version

    try:
        tag_name = await _fetch_latest_tag()
        _cached_version = tag_name.lstrip("v") or None
        _cache_ttl = SUCCESS_CACHE_TTL_SECONDS
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.warning("Could not check for the latest Corvid release: %s", e)
        _cache_ttl = FAILURE_CACHE_TTL_SECONDS
    finally:
        _cached_at = time.monotonic()

    return _cached_version
