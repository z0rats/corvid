"""Quick Steam profile lookup: a handful of Steam Web API calls (summary, bans, level, game count)
plus the keyless location-name resolution, with no friends-graph work - that's the scan's job.
"""

import asyncio
import logging
from collections.abc import Awaitable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.features.steam_recon.config.steam_recon_config import build_quick_links
from app.features.steam_recon.schemas.steam_recon_schemas import (
    ProfileRequest,
    ProfileResponse,
    QuickLink,
    SteamBans,
    SteamLocation,
    SteamProfile,
    Visibility,
)
from app.features.steam_recon.service.steam_api_client import (
    SteamApiClient,
    SteamApiError,
    SteamKeyRejectedError,
    SteamRateLimitedError,
)
from app.features.steam_recon.service.steam_api_key_service import get_steam_api_key
from app.features.steam_recon.service.steam_locations_service import resolve_location_names
from app.features.steam_recon.utils.steam_id_utils import parse_steam_target

logger = logging.getLogger(__name__)

VISIBILITY_BY_STATE: dict[int, Visibility] = {1: "private", 2: "friends_only", 3: "public"}


def steam_error_to_http(exc: SteamApiError) -> AppHTTPException:
    """The HTTP error a Steam client failure maps to, shared by the profile lookup and the scan."""
    if isinstance(exc, SteamKeyRejectedError):
        return AppHTTPException(
            status_code=403,
            detail=(
                "Steam rejected the API key. Check it under Settings > API Keys - the Steam "
                "account behind it must not be limited."
            ),
            error_code="STEAM_KEY_REJECTED",
        )
    if isinstance(exc, SteamRateLimitedError):
        return AppHTTPException(
            status_code=429,
            detail="Steam Web API rate limit reached, try again later",
            error_code="STEAM_RATE_LIMITED",
        )
    return AppHTTPException(
        status_code=502,
        detail="Steam Web API request failed",
        error_code="STEAM_API_ERROR",
    )


async def optional[T](call: Awaitable[T]) -> T | None:
    """Run a nice-to-have call: private/failed data becomes None, but a rejected key or a rate
    limit still propagates, since every later call would hit the same wall."""
    try:
        return await call
    except SteamKeyRejectedError, SteamRateLimitedError:
        raise
    except SteamApiError:
        return None


def map_bans(raw: dict[str, Any] | None) -> SteamBans | None:
    if not raw:
        return None
    return SteamBans(
        community_banned=bool(raw.get("CommunityBanned")),
        vac_banned=bool(raw.get("VACBanned")),
        number_of_vac_bans=int(raw.get("NumberOfVACBans") or 0),
        days_since_last_ban=int(raw.get("DaysSinceLastBan") or 0),
        number_of_game_bans=int(raw.get("NumberOfGameBans") or 0),
        economy_ban=str(raw.get("EconomyBan") or "none"),
    )


async def map_location(summary: dict[str, Any]) -> SteamLocation | None:
    country_code = summary.get("loccountrycode")
    if not country_code:
        return None
    state_code = summary.get("locstatecode")
    city_id = summary.get("loccityid")
    names = await resolve_location_names(country_code, state_code, city_id)
    return SteamLocation(
        country_code=country_code,
        state_code=state_code,
        city_id=city_id,
        country=names["country"],
        state=names["state"],
        city=names["city"],
    )


async def resolve_steamid64(client: SteamApiClient, raw_target: str) -> str:
    target = parse_steam_target(raw_target)
    if target is None:
        raise AppHTTPException(
            status_code=400,
            detail="Not a recognized Steam ID, profile URL or vanity name",
            error_code="STEAM_INVALID_TARGET",
        )
    if target.kind == "steamid64":
        return target.value

    steamid64 = await client.resolve_vanity(target.value)
    if not steamid64:
        raise AppHTTPException(
            status_code=404,
            detail=f"No Steam profile uses the vanity name '{target.value}'",
            error_code="STEAM_PROFILE_NOT_FOUND",
        )
    return steamid64


async def perform_profile_lookup(request: ProfileRequest, db: AsyncSession) -> ProfileResponse:
    """Look up a Steam profile.

    Raises:
        AppHTTPException: On an unrecognized target, a missing/rejected API key, an unknown
            profile, a rate limit, or a Steam outage.
    """
    api_key = await get_steam_api_key(db)
    if not api_key:
        raise AppHTTPException(
            status_code=400,
            detail="A Steam Web API key is required. Add one under Settings > API Keys.",
            error_code="STEAM_NOT_CONFIGURED",
        )

    try:
        async with SteamApiClient(api_key) as client:
            steamid64 = await resolve_steamid64(client, request.target)
            summaries, bans, level, game_count = await asyncio.gather(
                client.get_player_summaries([steamid64]),
                optional(client.get_player_bans([steamid64])),
                optional(client.get_steam_level(steamid64)),
                optional(client.get_owned_games_count(steamid64)),
            )
    except SteamApiError as exc:
        raise steam_error_to_http(exc) from exc

    summary = summaries.get(steamid64)
    if summary is None:
        raise AppHTTPException(
            status_code=404,
            detail="Steam returned no profile for this ID",
            error_code="STEAM_PROFILE_NOT_FOUND",
        )

    profile = SteamProfile(
        steamid64=steamid64,
        persona_name=summary.get("personaname"),
        real_name=summary.get("realname"),
        profile_url=summary.get("profileurl"),
        avatar_url=summary.get("avatarfull"),
        visibility=VISIBILITY_BY_STATE.get(summary.get("communityvisibilitystate", 0), "unknown"),
        created_at=summary.get("timecreated"),
        last_logoff=summary.get("lastlogoff"),
        location=await map_location(summary),
        level=level,
        game_count=game_count,
        bans=map_bans((bans or {}).get(steamid64)),
    )
    return ProfileResponse(
        profile=profile,
        quick_links=[QuickLink(**link) for link in build_quick_links(steamid64)],
    )
