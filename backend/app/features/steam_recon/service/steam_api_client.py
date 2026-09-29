"""Steam Web API client (https://api.steampowered.com) - fixed host. Every method needs the key
configured under Settings > API Keys ("steam").

The key travels in the `key=` query parameter (Steam has no header option), so nothing here logs a
request URL or `str()` of an httpx error - `SecretRedactionFilter` would catch it, but not
emitting it is the safer default.
"""

import logging
from collections.abc import Iterator
from types import TracebackType
from typing import Any, Self

import httpx

from app.features.steam_recon.config.cheater_scoring_config import CS2_APPID
from app.features.steam_recon.config.steam_recon_config import (
    PLAYER_BATCH_SIZE,
    STEAM_API_BASE_URL,
    STEAM_API_TIMEOUT,
)

logger = logging.getLogger(__name__)


class SteamApiError(Exception):
    """Base class for a Steam Web API request that didn't produce usable data."""


class SteamKeyRejectedError(SteamApiError):
    """HTTP 403: the key is invalid, revoked, or the account behind it is restricted."""


class SteamPrivateError(SteamApiError):
    """HTTP 401: the requested data (usually a friends list) is private."""


class SteamRateLimitedError(SteamApiError):
    """HTTP 429: the key's quota or burst limit was hit."""

    def __init__(self, retry_after: float | None = None):
        super().__init__("Steam Web API rate limit hit")
        self.retry_after = retry_after


def _chunks(items: list[str], size: int) -> Iterator[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _parse_retry_after(response: httpx.Response) -> float | None:
    try:
        return float(response.headers["Retry-After"])
    except KeyError, ValueError:
        return None


class SteamApiClient:
    """One shared connection pool for a whole lookup/scan. Use as `async with`."""

    def __init__(self, api_key: str, *, transport: httpx.AsyncBaseTransport | None = None):
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=STEAM_API_BASE_URL, timeout=STEAM_API_TIMEOUT, transport=transport
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._client.aclose()

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        try:
            response = await self._client.get(path, params={"key": self._api_key, **params})
        except httpx.HTTPError as exc:
            # str(exc) can embed the request URL, and with it the key.
            logger.warning("Steam Web API request to %s failed: %s", path, type(exc).__name__)
            raise SteamApiError("Steam Web API is unreachable") from None

        if response.status_code == 429:
            raise SteamRateLimitedError(_parse_retry_after(response))
        if response.status_code == 403:
            raise SteamKeyRejectedError("Steam Web API rejected the key")
        if response.status_code == 401:
            raise SteamPrivateError("Steam data is private")
        if response.status_code != 200:
            logger.warning("Steam Web API %s returned status %s", path, response.status_code)
            raise SteamApiError(f"Steam Web API returned status {response.status_code}")

        try:
            data = response.json()
        except ValueError:
            raise SteamApiError("Steam Web API returned a non-JSON response") from None
        return data if isinstance(data, dict) else {}

    async def resolve_vanity(self, vanity: str) -> str | None:
        """SteamID64 for a vanity name, or None if no profile uses it (`success` 42)."""
        data = await self._get("/ISteamUser/ResolveVanityURL/v1/", vanityurl=vanity)
        body = data.get("response") or {}
        steamid = body.get("steamid")
        return str(steamid) if body.get("success") == 1 and steamid else None

    async def get_player_summaries(self, steamids: list[str]) -> dict[str, dict[str, Any]]:
        """Profile summaries keyed by SteamID64; private/nonexistent accounts may be absent."""
        result: dict[str, dict[str, Any]] = {}
        for chunk in _chunks(steamids, PLAYER_BATCH_SIZE):
            data = await self._get("/ISteamUser/GetPlayerSummaries/v2/", steamids=",".join(chunk))
            for player in (data.get("response") or {}).get("players") or []:
                if player.get("steamid"):
                    result[str(player["steamid"])] = player
        return result

    async def get_player_bans(self, steamids: list[str]) -> dict[str, dict[str, Any]]:
        """Ban records keyed by SteamID64."""
        result: dict[str, dict[str, Any]] = {}
        for chunk in _chunks(steamids, PLAYER_BATCH_SIZE):
            data = await self._get("/ISteamUser/GetPlayerBans/v1/", steamids=",".join(chunk))
            for player in data.get("players") or []:
                if player.get("SteamId"):
                    result[str(player["SteamId"])] = player
        return result

    async def get_steam_level(self, steamid: str) -> int | None:
        data = await self._get("/IPlayerService/GetSteamLevel/v1/", steamid=steamid)
        level = (data.get("response") or {}).get("player_level")
        return level if isinstance(level, int) else None

    async def get_owned_games_count(self, steamid: str) -> int | None:
        """Number of owned games, or None when the game library is private (no `game_count`)."""
        data = await self._get(
            "/IPlayerService/GetOwnedGames/v1/", steamid=steamid, include_played_free_games=1
        )
        count = (data.get("response") or {}).get("game_count")
        return count if isinstance(count, int) else None

    async def get_friend_list(self, steamid: str) -> list[dict[str, Any]] | None:
        """This account's friends (`{steamid, friend_since}`), or None if the friends list is
        private. `SteamPrivateError` (HTTP 401) is Steam's actual signal for this - caught here
        rather than left to the caller, since "private friends list" is routine for a scan
        walking hundreds of friends, not an error worth surfacing per-friend."""
        try:
            data = await self._get(
                "/ISteamUser/GetFriendList/v1/", steamid=steamid, relationship="friend"
            )
        except SteamPrivateError:
            return None
        return (data.get("friendslist") or {}).get("friends")

    async def get_cs2_stats(self, steamid: str) -> dict[str, int] | None:
        """Raw CS2 (appid 730) user stats by name, or None if unavailable (private game
        details, or the account has never played)."""
        try:
            data = await self._get(
                "/ISteamUserStats/GetUserStatsForGame/v2/", steamid=steamid, appid=CS2_APPID
            )
        except SteamApiError:
            return None
        stats = (data.get("playerstats") or {}).get("stats")
        if not stats:
            return None
        return {s["name"]: s["value"] for s in stats if "name" in s and "value" in s}
