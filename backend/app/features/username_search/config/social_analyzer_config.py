import json
import logging
import shutil
from functools import lru_cache
from importlib import metadata as importlib_metadata

import httpx

PACKAGE_NAME = "social-analyzer"
BINARY_NAME = "social-analyzer"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"

# Hard ceiling on total subprocess runtime, independent of the per-site
# `--timeout`/`--top` CLI flags (which can be user-configured to 0 = unbounded).
# Guards against a hung/runaway subprocess never being reaped when nothing
# calls cancel_scan() and no client is waiting on the SSE stream.
PROCESS_WATCHDOG_SECONDS = 1800

logger = logging.getLogger(__name__)


def find_binary() -> str | None:
    """Locate the installed social-analyzer console script on PATH"""
    return shutil.which(BINARY_NAME)


@lru_cache
def get_installed_version() -> str:
    """Installed social-analyzer package version, read from package metadata
    (no import needed - the package's on-disk module can't be imported as a
    regular Python module since its directory name contains a hyphen)."""
    return importlib_metadata.version(PACKAGE_NAME)


@lru_cache
def get_bundled_site_count() -> int:
    """Number of sites in the site database bundled with the installed package"""
    dist = importlib_metadata.distribution(PACKAGE_NAME)
    sites_path = next(f for f in dist.files if f.name == "sites.json")
    with open(dist.locate_file(sites_path), encoding="utf-8") as f:
        data = json.load(f)
    return len(data.get("websites_entries", []))


async def fetch_latest_pypi_version(timeout_seconds: float = 5.0) -> str | None:
    """Check PyPI for the latest published social-analyzer version.

    Returns None on any network/parsing error rather than raising - this is
    a best-effort "is an update available" check, not a required operation.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(PYPI_JSON_URL)
            response.raise_for_status()
            return response.json()["info"]["version"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Failed to check PyPI for latest social-analyzer version: %s", exc)
        return None
