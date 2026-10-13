"""Pivot material for a finished username run: other handles, names and emails Maigret parsed out
of the found profiles, ranked and classified. Everything here is a lead, not attribution - a
shared handle is often a different person.

Profile links are resolved to a (site, handle) pair in two tiers. A short table of well-known
platforms (`_KNOWN_PROFILES`) goes first because Maigret's site database is a probing database,
not a link resolver: its templates miss `x.com`, need `/about` for YouTube and capture whole
paths on greedy ones. Everything else falls back to the database with strict validation."""

import re
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlsplit

from maigret.sites import MaigretDatabase, MaigretSite

from app.features.username_search.config.maigret_config import get_maigret_database
from app.features.username_search.schemas.username_search_schemas import (
    PivotEmail,
    PivotName,
    PivotUsername,
    RunPivots,
)

MAX_PIVOTS_PER_KIND = 60

# (Maigret site name, profile-URL pattern on host + path with the scheme, `www.` and any
# query/fragment/trailing slash already stripped). Each site name must exist in Maigret's
# database - tests/features/username_search/test_pivot_service.py enforces it, since a named
# site check later needs the exact name.
_KNOWN_PROFILES: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (site, re.compile(pattern, re.IGNORECASE))
    for site, pattern in (
        ("GitHub", r"github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))"),
        ("GitLab", r"gitlab\.com/([A-Za-z0-9_.-]{2,255})"),
        ("Twitter", r"(?:mobile\.)?(?:twitter|x)\.com/([A-Za-z0-9_]{1,15})"),
        ("Instagram", r"instagram\.com/([A-Za-z0-9._]{1,30})"),
        ("Facebook", r"(?:m\.)?facebook\.com/([A-Za-z0-9.]{5,50})"),
        ("LinkedIn", r"(?:[a-z]{2,3}\.)?linkedin\.com/in/([A-Za-z0-9_%-]{3,100})"),
        ("YouTube", r"(?:m\.)?youtube\.com/@([A-Za-z0-9._-]{3,30})"),
        ("Reddit", r"(?:old\.)?reddit\.com/(?:u|user)/([A-Za-z0-9_-]{3,20})"),
        ("Telegram", r"(?:t|telegram)\.me/([A-Za-z0-9_]{5,32})"),
        ("Medium", r"medium\.com/@([A-Za-z0-9_.-]{1,40})"),
        ("Keybase", r"keybase\.io/([A-Za-z0-9_]{2,16})"),
        ("TikTok", r"tiktok\.com/@([A-Za-z0-9._]{2,24})"),
        ("Pinterest", r"pinterest\.com/([A-Za-z0-9_]{3,30})"),
        ("Vimeo", r"vimeo\.com/([A-Za-z0-9_-]{2,40})"),
        ("SoundCloud", r"soundcloud\.com/([A-Za-z0-9_-]{3,25})"),
        ("Behance", r"behance\.net/([A-Za-z0-9_-]{3,30})"),
        ("Dribbble", r"dribbble\.com/([A-Za-z0-9_-]{2,30})"),
        ("VK", r"vk\.com/([A-Za-z0-9_.]{3,32})"),
        ("Patreon", r"patreon\.com/([A-Za-z0-9_-]{3,40})"),
        ("About.me", r"about\.me/([A-Za-z0-9_.-]{2,40})"),
    )
)

# Page names that sit where a handle would on the same sites; resolving them to a "person"
# would suggest searching for "settings".
_RESERVED_HANDLES = frozenset(
    "about account accounts api apps explore feed followers following help home i intent "
    "jobs login logout messages notifications privacy pricing search settings share signup "
    "status support terms tos user users watch www".split()
)
_HANDLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{1,63}")

# Link shorteners hide the real target and are never followed, so they are dead ends.
_SHORTENER_HOSTS = frozenset(
    "bit.ly t.co goo.gl tinyurl.com ow.ly buff.ly is.gd lnkd.in youtu.be fb.me wp.me".split()
)

# Platforms the host index lacks (the `_KNOWN_PROFILES` table exists because of these gaps).
_EXTRA_PLATFORM_HOSTS = frozenset(
    "x.com twitter.com mobile.twitter.com youtube.com m.youtube.com facebook.com t.me "
    "telegram.me linkedin.com".split()
)

_NON_PROFILE_SITE_MARKERS = ("Archive.org", "(Group)", "(by id)")

# Role mailboxes, RFC 2606 placeholders / reserved TLDs and GitHub's noreply relay reach
# nobody useful. `hello@`/`contact@` stay: that is how a freelancer takes mail.
_ROLE_LOCALS = frozenset(
    "noreply no-reply donotreply do-not-reply postmaster mailer-daemon abuse".split()
)
_PLACEHOLDER_DOMAINS = frozenset({"example.com", "example.net", "example.org"})
_RESERVED_TLDS = frozenset({"test", "invalid", "localhost", "example"})
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


def normalize_profile_url(url: str) -> tuple[str, str] | None:
    """Split a link into (host without `www.`, path without query/fragment/trailing slash)."""
    try:
        parts = urlsplit(url.strip())
    except ValueError:
        return None
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        return None
    host = parts.hostname.lower()
    host = host.removeprefix("www.")
    return host, parts.path.rstrip("/")


def _usable_handle(handle: str) -> bool:
    return bool(_HANDLE.fullmatch(handle)) and handle.lower() not in _RESERVED_HANDLES


def _site_host_key(site: MaigretSite) -> str | None:
    """Host a site's profile URLs live on, keyed so a link can find its candidate sites
    without testing every site's regexp. A `{username}.host` template is keyed by `host`."""
    template = getattr(site, "url", None)
    if not template or "{username}" not in template or "?" in template or "*" in template:
        return None
    if any(marker in site.name for marker in _NON_PROFILE_SITE_MARKERS):
        return None
    template = template.replace("{urlMain}", site.url_main).replace(
        "{urlSubpath}", getattr(site, "url_subpath", "")
    )
    host = urlsplit(template.replace("{username}", "x")).hostname
    if not host:
        return None
    host = host.lower().removeprefix("www.")
    return host.removeprefix("x.") if "{username}." in template else host


_index_cache: tuple[MaigretDatabase, dict[str, list[MaigretSite]]] | None = None


def _host_index(db: MaigretDatabase) -> dict[str, list[MaigretSite]]:
    """Enabled username-type sites by host. Rebuilt when the database object is replaced
    (`reload_maigret_database` after a refresh)."""
    global _index_cache
    if _index_cache is not None and _index_cache[0] is db:
        return _index_cache[1]
    index: dict[str, list[MaigretSite]] = {}
    for site in db.sites:
        if site.disabled or site.type != "username" or not site.url_regexp:
            continue
        key = _site_host_key(site)
        if key:
            index.setdefault(key, []).append(site)
    _index_cache = (db, index)
    return index


def _host_keys(host: str) -> set[str]:
    labels = host.split(".")
    return {host, *(".".join(labels[i:]) for i in range(1, len(labels) - 1))}


def is_platform_host(host: str, db: MaigretDatabase | None = None) -> bool:
    """Whether a host belongs to a site Maigret (or the well-known table) knows as a profile
    platform - as opposed to a personal domain."""
    host = host.lower().removeprefix("www.")
    if host in _SHORTENER_HOSTS or host in _EXTRA_PLATFORM_HOSTS:
        return True
    index = _host_index(db or get_maigret_database())
    return any(key in index for key in _host_keys(host))


def resolve_profile_link(url: str, db: MaigretDatabase | None = None) -> tuple[str, str] | None:
    """(Maigret site name, handle) a profile link points to, or None when it is not a recognised
    profile (a site page, a deep path, a root domain, a shortener)."""
    normalized = normalize_profile_url(url)
    if normalized is None:
        return None
    host, path = normalized
    if host in _SHORTENER_HOSTS:
        return None
    candidate = f"{host}{path}"

    for site_name, pattern in _KNOWN_PROFILES:
        match = pattern.fullmatch(candidate)
        if match and _usable_handle(match.group(1)):
            return site_name, match.group(1)

    index = _host_index(db or get_maigret_database())
    keys = _host_keys(host)
    canonical = f"https://{host}{path}"
    for key in keys:
        for site in index.get(key, ()):
            found = site.extract_id_from_url(canonical)
            if found and _usable_handle(found[0]):
                return site.name, found[0]
    return None


def extract_emails(value: Any) -> list[str]:
    """Plausible personal addresses in a profile field (a string, or a list of strings)."""
    texts = value if isinstance(value, list) else [value]
    found: list[str] = []
    for text in texts:
        if not isinstance(text, str):
            continue
        for address in _EMAIL.findall(text):
            email = address.lower()
            local, _, domain = email.partition("@")
            if (
                local in _ROLE_LOCALS
                or domain in _PLACEHOLDER_DOMAINS
                or domain.rsplit(".", 1)[-1] in _RESERVED_TLDS
                or domain == "users.noreply.github.com"
                or email in found
            ):
                continue
            found.append(email)
    return found


def build_pivots(
    found_sites: Iterable[tuple[str, dict | None]],
    searched_username: str,
    db: MaigretDatabase | None = None,
) -> RunPivots:
    """Aggregate pivots across a run's found sites, given `(site_name, extra)` pairs.

    Handles come in two kinds: `reported` (the profile page itself named another account) and
    `link` (a URL the owner put on the profile, resolved to the account it points at). A handle
    seen both ways is `reported`. Non-handle IDs (a VK or Steam ID) are kept but not
    searchable, since a username search for a numeric ID wastes a whole scan."""
    self_key = searched_username.strip().lower()
    usernames: dict[str, PivotUsername] = {}
    names: dict[str, PivotName] = {}
    emails: dict[str, PivotEmail] = {}

    def add_username(value: str, kind: str, id_type: str, site: str | None, source: str) -> None:
        key = value.strip().lower()
        if not key or key == self_key:
            return
        entry = usernames.get(key)
        if entry is None:
            entry = usernames[key] = PivotUsername(
                value=value.strip(),
                kind=kind,
                id_type=id_type,
                searchable=id_type == "username",
                site=site,
                sites=[],
            )
        elif kind == "reported" and entry.kind == "link":
            entry.kind, entry.id_type, entry.searchable = kind, id_type, id_type == "username"
        entry.site = entry.site or site
        if source not in entry.sites:
            entry.sites.append(source)

    def add_plain(bucket: dict, model: type, value: str, source: str) -> None:
        key = value.strip().lower()
        if not key:
            return
        entry = bucket.setdefault(key, model(value=value.strip(), sites=[]))
        if source not in entry.sites:
            entry.sites.append(source)

    for site_name, extra in found_sites:
        if not extra:
            continue
        for item in extra.get("discovered_usernames") or []:
            add_username(item["value"], "reported", item.get("type") or "username", None, site_name)
        for link in extra.get("discovered_links") or []:
            resolved = resolve_profile_link(link, db)
            if resolved:
                link_site, handle = resolved
                add_username(handle, "link", "username", link_site, site_name)
        for name in extra.get("discovered_names") or []:
            add_plain(names, PivotName, name, site_name)
        for email in extra.get("discovered_emails") or []:
            add_plain(emails, PivotEmail, email, site_name)

    ranked = sorted(
        usernames.values(),
        key=lambda u: (not u.searchable, u.kind != "reported", -len(u.sites), u.value.lower()),
    )
    return RunPivots(
        usernames=ranked[:MAX_PIVOTS_PER_KIND],
        names=list(names.values())[:MAX_PIVOTS_PER_KIND],
        emails=list(emails.values())[:MAX_PIVOTS_PER_KIND],
    )
