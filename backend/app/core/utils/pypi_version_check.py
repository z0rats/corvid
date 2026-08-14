"""Single copy of the "check PyPI for a newer version of this vendored OSINT tool"
pattern shared by `username_search` (maigret, social-analyzer) and `email_search`
(mailcat-osint). Was three near-identical fetch+record+bool blocks before this
existed. See docs/database-schema-audit.md section 6, phase 3 addendum.
"""

import datetime
import logging
from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.mixins import PypiVersionCheckMixin

logger = logging.getLogger(__name__)


@dataclass
class UpdateCheckResult:
    latest_version: str | None
    update_available: bool | None


def compute_update_available(
    latest_pypi_version: str | None, installed_version: str
) -> bool | None:
    """None if never checked, else latest != installed"""
    if latest_pypi_version is None:
        return None
    return latest_pypi_version != installed_version


async def fetch_latest_pypi_version(package_name: str, timeout_seconds: float = 5.0) -> str | None:
    """Check PyPI for the latest published version of a package.

    Returns None on any network/parsing error rather than raising - this is
    a best-effort "is an update available" check, not a required operation.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(f"https://pypi.org/pypi/{package_name}/json")
            response.raise_for_status()
            return response.json()["info"]["version"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Failed to check PyPI for latest %s version: %s", package_name, exc)
        return None


async def record_pypi_check(
    db: AsyncSession, config: PypiVersionCheckMixin, latest_version: str | None
) -> None:
    """Persist the result of a PyPI check onto any config row using `PypiVersionCheckMixin`"""
    config.latest_pypi_version = latest_version
    config.pypi_checked_at = datetime.datetime.now(datetime.UTC)
    await db.flush()
    await db.refresh(config)


async def check_for_update(
    db: AsyncSession, package_name: str, config: PypiVersionCheckMixin, installed_version: str
) -> UpdateCheckResult:
    """Fetch the latest PyPI version, persist it, and compute update availability -
    the full orchestration used by every check-update endpoint"""
    latest_version = await fetch_latest_pypi_version(package_name)
    await record_pypi_check(db, config, latest_version)
    return UpdateCheckResult(
        latest_version=latest_version,
        update_available=compute_update_available(latest_version, installed_version),
    )
