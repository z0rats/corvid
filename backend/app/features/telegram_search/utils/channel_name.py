"""Turns whatever an analyst pastes for a Telegram channel into its canonical username."""

import re
from urllib.parse import parse_qs, urlsplit

# Telegram usernames: 4-32 characters (4 only for auctioned names), Latin letters, digits and
# underscores, starting with a letter. Case-insensitive, so the canonical form is lowercase.
_USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{3,31}$")
_TME_HOSTS = frozenset({"t.me", "www.t.me", "telegram.me", "www.telegram.me", "telegram.dog"})
# First path segments of t.me links that are not a username (`/s/<name>` is the message preview).
RESERVED_PATHS = frozenset(
    {
        "addemoji",
        "addlist",
        "addstickers",
        "addtheme",
        "bg",
        "boost",
        "c",
        "iv",
        "joinchat",
        "login",
        "proxy",
        "setlanguage",
        "share",
        "socks",
    }
)
PRIVATE_LINK_MESSAGE = (
    "This is a private invite link - only public channels and groups (with a @username) can be "
    "analyzed"
)


def _username_from_url(text: str) -> str:
    parsed = urlsplit(text if "://" in text else f"https://{text}")
    if parsed.scheme == "tg":
        domain = parse_qs(parsed.query).get("domain", [""])[0]
        return domain
    if (parsed.hostname or "").lower() not in _TME_HOSTS:
        raise ValueError("Not a t.me link")
    segments = [s for s in parsed.path.split("/") if s]
    if segments and segments[0] == "s":
        segments = segments[1:]
    if not segments:
        raise ValueError("The link has no channel name")
    first = segments[0]
    if first.startswith("+") or first.lower() in {"joinchat", "c"}:
        raise ValueError(PRIVATE_LINK_MESSAGE)
    if first.lower() in RESERVED_PATHS:
        raise ValueError("This t.me link is not a channel")
    return first


def normalize_channel(raw: str) -> str:
    """Canonical lowercase username from `@name`, `name`, `t.me/name`, `t.me/s/name`,
    `t.me/name/123`, `telegram.me/name` or `tg://resolve?domain=name`. Raises `ValueError` with a
    user-facing message for anything else."""
    text = raw.strip()
    if not text:
        raise ValueError("Channel cannot be empty")
    if text.startswith("@"):
        candidate = text[1:]
    elif "/" in text or text.lower().startswith("tg:"):
        candidate = _username_from_url(text)
    else:
        candidate = text
    candidate = candidate.lower()
    if not _USERNAME_RE.match(candidate):
        raise ValueError(
            "Not a valid Telegram username - expected @name or a t.me link, 4-32 characters of "
            "Latin letters, digits and underscores"
        )
    return candidate
