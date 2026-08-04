"""Reverse geocoding (coordinates -> human-readable address) via OpenStreetMap's
Nominatim, the same no-API-key service already used for the embedded map on the
frontend. Best-effort only: a geocoder outage shouldn't fail the whole image
analysis, so this logs and returns None on any failure rather than raising.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_TIMEOUT = 8.0
# Nominatim's usage policy requires a descriptive User-Agent identifying the app.
HEADERS = {"User-Agent": "Corvid-ImageTools/1.0 (self-hosted OSINT tool)"}


async def _fetch_nominatim(latitude: float, longitude: float) -> dict:
    params = {"format": "jsonv2", "lat": latitude, "lon": longitude, "zoom": 14}
    async with httpx.AsyncClient(timeout=NOMINATIM_TIMEOUT, headers=HEADERS) as client:
        response = await client.get(NOMINATIM_URL, params=params)
        response.raise_for_status()
        return response.json()


async def reverse_geocode(latitude: float, longitude: float) -> str | None:
    try:
        data = await _fetch_nominatim(latitude, longitude)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
        logger.warning("Reverse geocoding failed for %s,%s: %s", latitude, longitude, e)
        return None

    address = data.get("display_name")
    return str(address) if address else None
