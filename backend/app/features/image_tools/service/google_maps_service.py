"""Fetches the optional Google Maps key configured under Settings > API Keys.

Unlike every other API key in this app, this one is consumed directly by the
browser (Google's Maps Embed API is designed to be used client-side) rather
than proxied through a server-side call - see image_routes.py's
/street-view-key route, the only place this raw value is exposed to the
frontend.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey

GOOGLE_MAPS_API_KEY_NAME = "google_maps"


async def get_google_maps_key(db: AsyncSession) -> str | None:
    """Returns the configured key, or None if unset/inactive."""
    apikey = await get_apikey(db=db, name=GOOGLE_MAPS_API_KEY_NAME)
    if apikey and apikey.is_active and apikey.key:
        return apikey.key
    return None
