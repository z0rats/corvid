"""Fetches the Steam Web API key configured under Settings > API Keys. Unlike YouTube's optional
key, this one is mandatory: every Steam Recon data source except comments needs it.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey

STEAM_API_KEY_NAME = "steam"


async def get_steam_api_key(db: AsyncSession) -> str | None:
    """Returns the configured key, or None if unset/inactive."""
    apikey = await get_apikey(db=db, name=STEAM_API_KEY_NAME)
    if apikey and apikey.is_active and apikey.key:
        return apikey.key
    return None
