"""Health/version reporting for the Instagram module. `latest_pypi_version` is a
best-effort, non-persisted check (see `core/utils/pypi_version_check.py`) - a
dedicated settings table just for this one field would be excessive, unlike
`username_search`/`email_search`'s vendored-tool version tracking.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.pypi_version_check import compute_update_available, fetch_latest_pypi_version
from app.features.instagram_search.config.instagram_search_config import PACKAGE_NAME
from app.features.instagram_search.schemas.instagram_search_schemas import (
    InstagramHealthResponse,
)
from app.features.instagram_search.service.instagram_session_service import is_session_configured

logger = logging.getLogger(__name__)


def get_installed_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        logger.error("%s is not installed despite being a declared dependency", PACKAGE_NAME)
        return "unknown"


async def get_health(db: AsyncSession) -> InstagramHealthResponse:
    installed_version = get_installed_version()
    latest_version = await fetch_latest_pypi_version(PACKAGE_NAME)
    return InstagramHealthResponse(
        installed_version=installed_version,
        latest_pypi_version=latest_version,
        update_available=compute_update_available(latest_version, installed_version),
        session_configured=await is_session_configured(db),
    )
