"""Maps a raw ChronoVerify verdict (chronoverify_api_service.py) into
ChronoverifyResponse. Opt-in only - unlike the rest of image_tools, this sends
the image to a third-party service, so the frontend gates it behind an explicit
user action rather than firing it automatically like the local anomaly/structure
panels.
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey

from ..schemas.image_schemas import (
    ChronoverifyC2pa,
    ChronoverifyCaptureDevice,
    ChronoverifyLocation,
    ChronoverifyResponse,
    ChronoverifySignal,
)
from .chronoverify_api_service import fetch_chronoverify_verdict

logger = logging.getLogger(__name__)

CHRONOVERIFY_API_KEY_NAME = "chronoverify"


async def _get_chronoverify_key(db: AsyncSession) -> str | None:
    """Returns the configured key, or None to fall back to the free keyless path."""
    apikey = await get_apikey(db=db, name=CHRONOVERIFY_API_KEY_NAME)
    if apikey and apikey.is_active and apikey.key:
        return apikey.key
    return None


async def check_image_provenance(
    filename: str, data: bytes, db: AsyncSession
) -> ChronoverifyResponse:
    """Submit an image to ChronoVerify and return its provenance/manipulation verdict."""
    api_key = await _get_chronoverify_key(db)
    logger.info(
        "Requesting ChronoVerify verdict for '%s' (%d bytes, keyed=%s)",
        filename,
        len(data),
        bool(api_key),
    )

    raw = await fetch_chronoverify_verdict(filename, data, api_key)

    result = ChronoverifyResponse(
        verdict=raw["verdict"],
        confidence=raw["confidence"],
        summary=raw["summary"],
        capture_time=_extract_capture_time(raw.get("capture_time")),
        capture_device=_parse_capture_device(raw.get("capture_device")),
        location=_parse_location(raw.get("capture_location")),
        c2pa=_parse_c2pa(raw.get("c2pa")),
        signals=_parse_signals(raw.get("signals")),
        sha256=raw.get("integrity", {}).get("sha256"),
    )

    logger.info("ChronoVerify verdict for '%s': %s", filename, result.verdict)
    return result


def _extract_capture_time(raw: dict[str, Any] | None) -> str | None:
    if not raw:
        return None
    value = raw.get("value")
    return str(value) if value else None


def _parse_capture_device(raw: dict[str, Any] | None) -> ChronoverifyCaptureDevice | None:
    if not raw:
        return None
    return ChronoverifyCaptureDevice(make=raw.get("make"), model=raw.get("model"))


def _parse_location(raw: dict[str, Any] | None) -> ChronoverifyLocation | None:
    if not raw:
        return None
    return ChronoverifyLocation(
        present=bool(raw.get("present")),
        place=raw.get("place"),
        city=raw.get("city"),
        region=raw.get("region"),
        country=raw.get("country"),
        latitude=raw.get("lat"),
        longitude=raw.get("lon"),
    )


def _parse_c2pa(raw: dict[str, Any] | None) -> ChronoverifyC2pa | None:
    if not raw:
        return None
    return ChronoverifyC2pa(present=bool(raw.get("present")), validated=bool(raw.get("validated")))


def _parse_signals(raw: list[dict[str, Any]] | None) -> list[ChronoverifySignal]:
    signals: list[ChronoverifySignal] = []
    for entry in raw or []:
        try:
            signals.append(
                ChronoverifySignal(
                    name=entry["name"],
                    layer=entry.get("layer", ""),
                    direction=entry.get("direction", "neutral"),
                    detail=entry.get("detail", ""),
                )
            )
        except (KeyError, TypeError) as e:
            logger.warning("Skipping malformed ChronoVerify signal entry: %s", e)
            continue
    return signals
