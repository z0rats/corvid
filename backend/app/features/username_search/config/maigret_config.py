import json
import logging
import os
import sys
from functools import lru_cache

import httpx
from maigret.db_updater import BUNDLED_DB_PATH, CACHED_DB_PATH
from maigret.sites import MaigretDatabase, MaigretSite

logger = logging.getLogger(__name__)

# Defaults mirror Maigret's own CLI/settings.json defaults (resources/settings.json),
# not the bare library function's fallback values, so a scan here behaves like
# `maigret <username>` run locally.
TIMEOUT_SECONDS_DEFAULT = 30
MAX_CONCURRENCY_DEFAULT = 100
TOP_SITES_COUNT_DEFAULT = 500  # 0 means "all sites" (CLI's --all-sites)
AUTO_UPDATE_DB_ENABLED_DEFAULT = True
AUTO_UPDATE_INTERVAL_HOURS_DEFAULT = 24  # matches Maigret's own autoupdate_check_interval_hours

PACKAGE_NAME = "maigret"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"


async def fetch_latest_pypi_version(timeout_seconds: float = 5.0) -> str | None:
    """Check PyPI for the latest published maigret version.

    Returns None on any network/parsing error rather than raising - this is
    a best-effort "is an update available" check, not a required operation.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(PYPI_JSON_URL)
            response.raise_for_status()
            return response.json()["info"]["version"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Failed to check PyPI for latest maigret version: %s", exc)
        return None


def _best_local_db_path() -> str:
    """Return the auto-updated cached DB if present and valid, else the bundled one.

    Reimplements Maigret's own `db_updater._best_local()` (a private helper)
    rather than importing it, to not depend on a third-party private API.
    """
    if os.path.isfile(CACHED_DB_PATH):
        try:
            with open(CACHED_DB_PATH, encoding="utf-8") as f:
                if "sites" in json.load(f):
                    return CACHED_DB_PATH
        except (json.JSONDecodeError, OSError):
            pass
    return BUNDLED_DB_PATH


@lru_cache
def get_maigret_database() -> MaigretDatabase:
    """Load Maigret's site database once per process.

    Prefers the auto-updated cache (`~/.maigret/data.json`) if one has been
    downloaded; otherwise falls back to the package's bundled
    resources/data.json - so this self-hosted tool works offline by default
    but benefits from `refresh_database()` when it has run.
    """
    return MaigretDatabase().load_from_file(_best_local_db_path())


def reload_maigret_database() -> MaigretDatabase:
    """Clear the cached site DB and reload from disk. Call after an update."""
    get_maigret_database.cache_clear()
    return get_maigret_database()


def get_site_dict(
    top_sites_count: int,
    tags: list[str] | None = None,
    excluded_tags: list[str] | None = None,
) -> dict[str, MaigretSite]:
    """Build the site dict to scan, ranked by popularity and optionally filtered by tag.

    ``top_sites_count`` of 0 scans every bundled site (CLI's --all-sites).
    """
    db = get_maigret_database()
    top = top_sites_count if top_sites_count > 0 else sys.maxsize
    return db.ranked_sites_dict(
        top=top,
        tags=tags or [],
        excluded_tags=excluded_tags or [],
        disabled=False,
        id_type="username",
    )


def get_available_tags() -> list[str]:
    """List all site category tags in the database (excluding country tags)."""
    from maigret.utils import is_country_tag

    db = get_maigret_database()
    tags = {tag for site in db.sites for tag in site.tags if not is_country_tag(tag)}
    return sorted(tags)
