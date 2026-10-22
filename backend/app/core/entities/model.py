"""The entity model shared by every feature's extractor: an entity is `(type, normalized value)`,
a link is `(source, target, relation)`. Extractors are pure functions of one stored run; the graph
(`graph.py`) merges what they return. See docs/adr/0028-entity-graph-derived-per-investigation.md.
"""

from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

EntityType = Literal[
    "ip",
    "domain",
    "url",
    "email",
    "hash",
    "cve",
    "wallet",
    "username",
    "account",
    "breach",
    "asn",
    "netblock",
    "subreddit",
]

ENTITY_TYPES: tuple[str, ...] = EntityType.__args__  # type: ignore[attr-defined]


def _normalize_domain(value: str) -> str:
    value = value.strip().rstrip(".").lower()
    try:
        return value.encode("idna").decode("ascii")
    except UnicodeError:
        return value


def _normalize_url(value: str) -> str:
    parts = urlsplit(value.strip())
    host = _normalize_domain(parts.hostname or "")
    netloc = f"{host}:{parts.port}" if parts.port else host
    return urlunsplit((parts.scheme.lower(), netloc, parts.path.rstrip("/"), parts.query, ""))


def _normalize_username(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("u/"):
        value = value[2:]
    return value.lstrip("@").lower()


def normalize(entity_type: str, value: str) -> str:
    """The value two features must agree on for their entities to meet in one node."""
    match entity_type:
        case "domain":
            return _normalize_domain(value)
        case "url":
            return _normalize_url(value) if "://" in value else value.strip()
        case "account":
            # Profile URLs differ only in case between tools (maigret's github.com/JDoe vs
            # Gravatar's github.com/jdoe) and usernames are case-insensitive almost everywhere.
            return (_normalize_url(value) if "://" in value else value.strip()).lower()
        case "username" | "subreddit":
            return _normalize_username(value)
        case "asn":
            return value.strip().upper()
        case "cve":
            return value.strip().upper()
        case "wallet":
            # EVM addresses are case-insensitive hex; the other chains are case-sensitive.
            stripped = value.strip()
            return stripped.lower() if stripped.lower().startswith("0x") else stripped
        case _:
            return value.strip().lower()


@dataclass(frozen=True)
class Entity:
    """One thing a run found or was about. `label` (display text) and `raw` (the value as the
    source gave it - the one to open or pivot with, since normalizing lowercases account URLs and
    usernames) are never compared."""

    type: str
    value: str
    label: str = field(default="", compare=False, hash=False)
    raw: str = field(default="", compare=False, hash=False)

    @property
    def id(self) -> str:
        return f"{self.type}:{self.value}"


def entity(entity_type: str, raw_value: str, label: str | None = None) -> Entity:
    """Build a normalized entity; `label` defaults to the raw value as the source gave it."""
    raw = raw_value.strip()
    return Entity(entity_type, normalize(entity_type, raw_value), label or raw, raw)


@dataclass(frozen=True)
class Link:
    source: Entity
    target: Entity
    relation: str


@dataclass
class Extraction:
    """What one run contributes to the graph. `root` is what the run was about (it gets the
    run's provenance even if no link touches it)."""

    root: Entity | None
    entities: list[Entity] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    def link(self, source: Entity, target: Entity, relation: str) -> None:
        if source == target:
            return
        self.entities.extend((source, target))
        self.links.append(Link(source, target, relation))

    def link_local_part(self, email: Entity) -> None:
        """email -> its local part as a username candidate, the pivot username search offers
        for an email (docs/adr/0025-email-username-candidates-in-username-search.md)."""
        local, sep, _domain = email.value.partition("@")
        local = local.split("+", 1)[0]
        if sep and local:
            self.link(email, entity("username", local), "local part")
