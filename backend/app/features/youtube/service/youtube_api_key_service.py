"""Fetches the optional YouTube Data API key configured under Settings > API Keys - shared
by youtube_lookup_service.py (extended stats tier) and youtube_comments_lookup_service.py
(comments have no keyless tier at all, so this key is mandatory there).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey

YOUTUBE_API_KEY_NAME = "youtube"


async def get_youtube_api_key(db: AsyncSession) -> str | None:
    """Returns the configured key, or None if unset/inactive."""
    apikey = await get_apikey(db=db, name=YOUTUBE_API_KEY_NAME)
    if apikey and apikey.is_active and apikey.key:
        return apikey.key
    return None
