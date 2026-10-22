"""Public Gravatar profile for an email address (keyless REST API v3).

Both requests go from the backend: the analyst's browser never contacts Gravatar, and the card
links the avatar rather than rendering it (ADR 0024).
"""

import hashlib
import logging
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx

from app.core.external_sources.contract import require_fields, require_list_field

from .client_base import get_client, handle_response, json_field

logger = logging.getLogger(__name__)

GRAVATAR_PROFILE_FIELDS = (
    "display_name",
    "profile_url",
    "avatar_url",
    "location",
    "description",
    "job_title",
    "company",
)
_GRAVATAR_NOT_FOUND = "Profile not found"
_GRAVATAR_ABOUT_LIMIT = 500

# A path segment that only introduces the username (`linkedin.com/in/<name>`,
# `reddit.com/user/<name>`, `steamcommunity.com/id/<vanity>`).
_USERNAME_PREFIX_SEGMENTS = {"in", "id", "u", "user", "users", "people"}
# A path segment that introduces a numeric or opaque id, not a username
# (`steamcommunity.com/profiles/<64-bit id>`, `facebook.com/app_scoped_user_id/<token>`).
_OPAQUE_ID_SEGMENTS = {"profiles", "channel", "app_scoped_user_id", "profile.php"}
# Hosts where the account is the subdomain (`<name>.tumblr.com`).
_SUBDOMAIN_ACCOUNT_HOSTS = {"tumblr.com", "wordpress.com", "blogspot.com", "substack.com"}


def gravatar_hash(email: str) -> str:
    """Gravatar's profile id: SHA-256 of the trimmed, lowercased address."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def username_from_account_url(url: str | None) -> str | None:
    """The username in a linked-account URL, or None when the URL holds an id instead
    (`github.com/beau` -> `beau`, `mastodon.social/@beau` -> `beau`, `linkedin.com/in/beau`
    -> `beau`, `beau.tumblr.com` -> `beau`, `facebook.com/profile.php?id=1` -> None).
    Gravatar gives each verified account's URL but no username field."""
    if not url:
        return None
    parts = urlsplit(url)
    if "id" in parse_qs(parts.query):
        return None
    segments = [segment for segment in parts.path.split("/") if segment]
    if segments and segments[0].lower() in _OPAQUE_ID_SEGMENTS:
        return None
    if segments and segments[0].lower() in _USERNAME_PREFIX_SEGMENTS:
        segments = segments[1:]
    if segments:
        name = segments[0].lstrip("@")
        return None if name.lower().endswith(".php") else name or None
    labels = (parts.hostname or "").split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in _SUBDOMAIN_ACCOUNT_HOSTS:
        return labels[0]
    return None


async def _has_custom_avatar(profile_hash: str) -> bool | None:
    """True if the address has its own avatar, False if `avatar_url` would only serve
    Gravatar's default image (`d=404` makes Gravatar answer 404 instead), None if unknown."""
    try:
        response = await get_client().head(
            f"https://www.gravatar.com/avatar/{profile_hash}", params={"d": "404"}
        )
    except httpx.RequestError as exc:
        logger.info("Gravatar avatar check failed: %s", exc)
        return None
    return {200: True, 404: False}.get(response.status_code)


def _truncate_about(about: Any) -> Any:
    if isinstance(about, str) and len(about) > _GRAVATAR_ABOUT_LIMIT:
        return about[:_GRAVATAR_ABOUT_LIMIT].rstrip() + "…"
    return about


async def check_gravatar(ioc: str) -> dict[str, Any]:
    """Display name, avatar, location, about and the linked accounts Gravatar verified (hidden
    ones dropped) for an email. No public profile is `found: false`, not an error. The keyless
    tier carries no `links`; only verified accounts."""
    logger.debug("Checking email %s with Gravatar", ioc)
    profile_hash = gravatar_hash(ioc)

    response = await get_client().get(url=f"https://api.gravatar.com/v3/profiles/{profile_hash}")
    if response.status_code == 404 and json_field(response, "error") == _GRAVATAR_NOT_FOUND:
        return {
            "found": False,
            **dict.fromkeys(GRAVATAR_PROFILE_FIELDS),
            "has_avatar": None,
            "verified_accounts": [],
        }
    result = await handle_response("Gravatar", response)
    require_fields(result, GRAVATAR_PROFILE_FIELDS, label="Gravatar")
    accounts = require_list_field(result, "verified_accounts", label="Gravatar")
    return {
        "found": True,
        **{field: result[field] for field in GRAVATAR_PROFILE_FIELDS},
        "description": _truncate_about(result["description"]),
        "has_avatar": await _has_custom_avatar(profile_hash),
        "verified_accounts": [
            _verified_account(account)
            for account in accounts
            if isinstance(account, dict) and not account.get("is_hidden")
        ],
    }


def _str_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _verified_account(account: dict[str, Any]) -> dict[str, str | None]:
    """One linked account, every field a string or None - the results are stored as-is and
    later fed to the entity graph, so a non-string from the provider must not get that far."""
    url = _str_or_none(account.get("url"))
    return {
        "service": _str_or_none(account.get("service_type")),
        "label": _str_or_none(account.get("service_label")),
        "url": url,
        "username": username_from_account_url(url),
    }
