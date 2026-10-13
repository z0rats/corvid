"""Triage of the profiles a follow-up search found, against what the run it followed already
knows (names, emails, personal domains, resolved accounts). Adapted from user-scanner's
cross-scan confidence idea; it ranks leads, it never drops one and is not attribution.

`confirmed`   the (site, handle) is itself a link the parent run's profiles published;
`likely`      the profile echoes an anchor: same name, same personal domain, same email, or a
              link to an account the parent already knows;
`conflicting` the profile shows a person's name that matches no anchor name;
`candidate`   nothing to compare, or nothing matched.

A name that merely restates the handle carries no information and is ignored, a name is read up
to its first comma (`Jane Doe, PhD`), and location is never used."""

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from maigret.sites import MaigretDatabase

from app.features.username_search.service.pivot_service import (
    build_pivots,
    is_platform_host,
    normalize_profile_url,
    resolve_profile_link,
)

CONFIDENCE_LEVELS = ("confirmed", "likely", "conflicting", "candidate")
_NON_ALNUM = re.compile(r"[^\w]+", re.UNICODE)


def _alnum(text: str) -> str:
    return _NON_ALNUM.sub("", text.casefold())


def name_key(name: str, handle: str) -> str | None:
    """Order-insensitive comparison key for a person's name, or None when it carries no
    information (empty, or just the handle again)."""
    first = name.split(",", 1)[0]
    tokens = sorted(token for token in _NON_ALNUM.split(first.casefold()) if token)
    if not tokens or "".join(tokens) == _alnum(handle) or _alnum(first) == _alnum(handle):
        return None
    return " ".join(tokens)


def personal_domain(link: str, db: MaigretDatabase | None = None) -> str | None:
    """Host of a link that points at a person's own site, not at a known platform."""
    normalized = normalize_profile_url(link)
    if normalized is None:
        return None
    host = normalized[0]
    if resolve_profile_link(link, db) or is_platform_host(host, db):
        return None
    return host


@dataclass
class Anchors:
    """What a parent run knows about its subject, for comparison with a follow-up's hits."""

    names: set[str] = field(default_factory=set)
    domains: set[str] = field(default_factory=set)
    emails: set[str] = field(default_factory=set)
    # (lower-case site, lower-case handle) the parent's profiles linked to
    pivot_accounts: set[tuple[str, str]] = field(default_factory=set)
    # pivot_accounts plus the parent's own claimed profiles
    known_accounts: set[tuple[str, str]] = field(default_factory=set)


def build_anchors(
    found_sites: Iterable[tuple[str, dict | None]],
    parent_username: str,
    db: MaigretDatabase | None = None,
) -> Anchors:
    """Anchors from the parent run's `(site_name, extra)` found-site pairs."""
    found_sites = list(found_sites)
    pivots = build_pivots(found_sites, parent_username, db)
    anchors = Anchors()
    for name in pivots.names:
        key = name_key(name.value, parent_username)
        if key:
            anchors.names.add(key)
    anchors.emails = {email.value for email in pivots.emails}
    for pivot in pivots.usernames:
        if pivot.site and pivot.searchable:
            anchors.pivot_accounts.add((pivot.site.lower(), pivot.value.lower()))
    anchors.known_accounts = set(anchors.pivot_accounts)
    for site_name, extra in found_sites:
        anchors.known_accounts.add((site_name.lower(), parent_username.lower()))
        for link in (extra or {}).get("discovered_links") or []:
            domain = personal_domain(link, db)
            if domain:
                anchors.domains.add(domain)
    return anchors


def classify_hit(
    site_name: str,
    extra: dict[str, Any] | None,
    username: str,
    anchors: Anchors,
    db: MaigretDatabase | None = None,
) -> str:
    """Confidence level of one found profile of `username` on `site_name`."""
    if (site_name.lower(), username.lower()) in anchors.pivot_accounts:
        return "confirmed"
    extra = extra or {}

    names = {key for n in extra.get("discovered_names") or [] if (key := name_key(n, username))}
    if names & anchors.names:
        return "likely"
    if anchors.emails & set(extra.get("discovered_emails") or []):
        return "likely"
    for link in extra.get("discovered_links") or []:
        domain = personal_domain(link, db)
        if domain and domain in anchors.domains:
            return "likely"
        resolved = resolve_profile_link(link, db)
        if resolved and (resolved[0].lower(), resolved[1].lower()) in anchors.known_accounts:
            return "likely"

    if names and anchors.names:
        return "conflicting"
    return "candidate"


def annotate_confidence(
    found_sites: list[dict], username: str, anchors: Anchors, db: MaigretDatabase | None = None
) -> None:
    """Set `extra["confidence"]` on each found-site row, in place."""
    for site in found_sites:
        level = classify_hit(site["site_name"], site.get("extra"), username, anchors, db)
        site["extra"] = {**(site.get("extra") or {}), "confidence": level}
