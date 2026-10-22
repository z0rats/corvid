"""ioc_lookup searches as investigation items: the single export's sections, plus the graph
entities a few providers' stored results carry (ASN, netblock, hostnames, linked accounts,
breaches)."""

import re
from collections.abc import Callable
from typing import Any

from app.core.entities.model import Entity, Extraction, entity
from app.core.run_sources.source import RunSource
from app.features.ioc_tools.ioc_lookup.single_lookup.crud.lookup_history_crud import (
    get_search_with_results,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupSearch,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.report_service import build_sections
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import IOC_TYPES

_HASH_TYPES = (IOC_TYPES["MD5"], IOC_TYPES["SHA1"], IOC_TYPES["SHA256"])
_NON_WALLET_TYPES = {
    IOC_TYPES["IPV4"]: "ip",
    IOC_TYPES["IPV6"]: "ip",
    IOC_TYPES["DOMAIN"]: "domain",
    IOC_TYPES["URL"]: "url",
    IOC_TYPES["EMAIL"]: "email",
    IOC_TYPES["CVE"]: "cve",
    **dict.fromkeys(_HASH_TYPES, "hash"),
}


def _entity_type(ioc_type: str) -> str | None:
    if ioc_type in _NON_WALLET_TYPES:
        return _NON_WALLET_TYPES[ioc_type]
    return "wallet" if ioc_type.endswith("Address") else None


_ASN_RE = re.compile(r"^\s*(?:AS)?(\d+)\b", re.IGNORECASE)


def _ip_geo(out: Extraction, root: Entity, data: dict[str, Any]) -> None:
    asn = data.get("asn")
    match = _ASN_RE.match(str(asn)) if asn is not None else None
    if match:
        out.link(root, entity("asn", f"AS{match.group(1)}", str(asn)), "announced by")


def _ip_rdap(out: Extraction, root: Entity, data: dict[str, Any]) -> None:
    owner = data.get("name") or "?"
    for cidr in data.get("cidrs") or []:
        out.link(root, entity("netblock", cidr, f"{cidr} ({owner})"), "in netblock")


def _internetdb(out: Extraction, root: Entity, data: dict[str, Any]) -> None:
    for hostname in data.get("hostnames") or []:
        out.link(root, entity("domain", hostname), "hostname")


def _gravatar(out: Extraction, root: Entity, data: dict[str, Any]) -> None:
    for account in data.get("verified_accounts") or []:
        url = account.get("url") if isinstance(account, dict) else None
        if not isinstance(url, str) or not url.strip():
            continue
        service = account.get("label") or account.get("service") or "account"
        username = account.get("username")
        node = entity("account", url, f"{service}: {username}" if username else service)
        out.link(root, node, "linked account")
        if username:
            out.link(node, entity("username", username), "username")


def _breach_names(data: Any) -> list[str]:
    """HIBP answers a list of breaches (`Name`); LeakCheck a dict with `sources` (`name`)."""
    if isinstance(data, list):
        return [item["Name"] for item in data if isinstance(item, dict) and item.get("Name")]
    sources = data.get("sources") if isinstance(data, dict) else None
    return [item["name"] for item in sources or [] if isinstance(item, dict) and item.get("name")]


def _breaches(out: Extraction, root: Entity, data: Any) -> None:
    for name in _breach_names(data):
        out.link(root, entity("breach", name), "breached in")


_PROVIDER_EXTRACTORS: dict[str, Callable[[Extraction, Entity, Any], None]] = {
    "ip_geo": _ip_geo,
    "ip_rdap": _ip_rdap,
    "internetdb": _internetdb,
    "gravatar": _gravatar,
    "haveibeenpwned": _breaches,
    "leakcheck": _breaches,
}


def extract_entities(search: SingleLookupSearch) -> Extraction:
    entity_type = _entity_type(search.ioc_type)
    if entity_type is None:
        return Extraction(root=None)
    root = entity(entity_type, search.ioc)
    out = Extraction(root=root)
    if entity_type == "email":
        out.link_local_part(root)
    for result in search.results:
        extractor = _PROVIDER_EXTRACTORS.get(result.service_key)
        if extractor is None or result.status != "found" or not result.data:
            continue
        data = result.data
        if isinstance(data, dict) or extractor is _breaches:
            extractor(out, root, data)
    return out


def _target(search: Any) -> str:
    return search.ioc


IOC_LOOKUP_RUN_SOURCE = RunSource(
    feature="ioc_lookup",
    label="IOC lookup",
    model=SingleLookupSearch,
    load=get_search_with_results,
    target=_target,
    build_sections=build_sections,
    extract=extract_entities,
)
