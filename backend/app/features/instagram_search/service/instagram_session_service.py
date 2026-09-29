"""Reads the optional Instagram session cookies configured under Settings > API
Keys (`instagram_session`) - imported from a logged-in browser session, never a
password login (see docs/architecture/instagram-search.md). Storage reuses the
existing encrypted `Apikey` row; this module only adds JSON/shape validation on
top of it. The raw value is never logged, only whether it parsed and had the
keys Instaloader requires.
"""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.features.instagram_search.config.instagram_search_config import (
    API_KEY_NAME,
    REQUIRED_SESSION_KEYS,
)

logger = logging.getLogger(__name__)


def _is_valid_session_dict(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    return all(isinstance(data.get(key), str) and data.get(key) for key in REQUIRED_SESSION_KEYS)


async def get_session_dict(db: AsyncSession) -> dict[str, str] | None:
    """Returns the configured Instagram session cookies as a dict, or None if
    unset, inactive, or malformed (invalid JSON / not a dict / missing one of
    `REQUIRED_SESSION_KEYS`) - callers should fall back to an anonymous lookup
    rather than fail the request outright.
    """
    apikey = await get_apikey(db=db, name=API_KEY_NAME)
    if not apikey or not apikey.is_active or not apikey.key:
        return None

    try:
        data = json.loads(apikey.key)
    except ValueError:
        logger.warning("Configured Instagram session is not valid JSON, ignoring it")
        return None

    if not _is_valid_session_dict(data):
        logger.warning(
            "Configured Instagram session is missing one of the required cookie keys %s, "
            "ignoring it",
            REQUIRED_SESSION_KEYS,
        )
        return None

    return data


async def is_session_configured(db: AsyncSession) -> bool:
    """Cheap boolean check for /health - reuses the same validation as the lookup."""
    return await get_session_dict(db) is not None
