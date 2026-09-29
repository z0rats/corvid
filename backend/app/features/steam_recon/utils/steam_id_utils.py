"""Parsing and conversion helpers for Steam identifiers (SteamID64/3/2, vanity, profile URLs).

Only ever extracts an ID or vanity name from user input - a user-supplied URL is never fetched
itself, so it can't be turned into an SSRF vector.
"""

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

# SteamID64 of an individual account = this base + the 32-bit account id.
STEAMID64_BASE = 76561197960265728
_ACCOUNT_ID_MAX = 2**32 - 1

_STEAMID64_RE = re.compile(r"^\d{17}$")
_STEAMID3_RE = re.compile(r"^\[?U:1:(\d{1,10})\]?$", re.IGNORECASE)
_STEAMID2_RE = re.compile(r"^STEAM_[0-5]:([01]):(\d{1,10})$", re.IGNORECASE)
_VANITY_RE = re.compile(r"^[A-Za-z0-9_-]{2,32}$")
_PROFILE_HOSTS = ("steamcommunity.com", "www.steamcommunity.com")


@dataclass(frozen=True)
class SteamTarget:
    """A normalized scan target: an already-resolved SteamID64, or a vanity name that still
    needs `ISteamUser/ResolveVanityURL` (or the keyless `?xml=1` fallback)."""

    kind: Literal["steamid64", "vanity"]
    value: str


def is_steamid64(value: str) -> bool:
    """Whether `value` is a 17-digit SteamID64 of an individual account."""
    if not _STEAMID64_RE.match(value):
        return False
    return STEAMID64_BASE < int(value) <= STEAMID64_BASE + _ACCOUNT_ID_MAX


def account_id_to_steamid64(account_id: int) -> str:
    """32-bit account id (e.g. a comment author's `data-miniprofile`) to SteamID64."""
    return str(STEAMID64_BASE + account_id)


def steamid64_to_account_id(steamid64: str) -> int:
    return int(steamid64) - STEAMID64_BASE


def _from_account_id(account_id: int) -> SteamTarget | None:
    if not 0 < account_id <= _ACCOUNT_ID_MAX:
        return None
    return SteamTarget("steamid64", account_id_to_steamid64(account_id))


def _parse_profile_url(raw: str) -> SteamTarget | None:
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    if (parsed.hostname or "").lower() not in _PROFILE_HOSTS:
        return None

    segments = [s for s in parsed.path.split("/") if s]
    if len(segments) < 2:
        return None
    kind, value = segments[0].lower(), segments[1]
    if kind == "profiles" and is_steamid64(value):
        return SteamTarget("steamid64", value)
    if kind == "id" and _VANITY_RE.match(value):
        return SteamTarget("vanity", value)
    return None


def parse_steam_target(raw: str) -> SteamTarget | None:
    """Normalize user input to a `SteamTarget`, or None if it isn't a recognizable Steam identity.

    Accepts a SteamID64, SteamID3 (`[U:1:N]`), SteamID2 (`STEAM_X:Y:Z`), a steamcommunity.com
    `/profiles/<id64>` or `/id/<vanity>` URL, or a bare vanity name. A 17-digit number outside
    the individual-account range is rejected rather than treated as a vanity name.
    """
    text = (raw or "").strip()
    if not text:
        return None

    if "/" in text or text.lower().startswith("http"):
        candidate = text if "://" in text else f"https://{text}"
        return _parse_profile_url(candidate)

    if _STEAMID64_RE.match(text):
        return SteamTarget("steamid64", text) if is_steamid64(text) else None

    if match := _STEAMID3_RE.match(text):
        return _from_account_id(int(match.group(1)))

    if match := _STEAMID2_RE.match(text):
        y, z = int(match.group(1)), int(match.group(2))
        return _from_account_id(z * 2 + y)

    if _VANITY_RE.match(text):
        return SteamTarget("vanity", text)
    return None
