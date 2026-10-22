"""Keyless IP context: geolocation/ASN (ipapi.is) and netblock ownership (RDAP).

Both refuse a non-public address (RFC 1918, loopback, link-local, CGNAT, documentation ranges,
...) before any request: there is nothing a third party can say about it, and sending it would
only leak the analyst's internal addressing. That answer is a result (`reserved: true`), not an
error.
"""

import ipaddress
import logging
from typing import Any

import httpx

from app.core.config.settings import settings
from app.core.external_sources.contract import require_fields
from app.core.security.ssrf_guard import SSRFValidationError, safe_get
from app.features.ioc_tools.domain_finder.service.whois_lookup_service import (
    extract_rdap_entities,
    extract_rdap_events,
)

from .client_base import (
    DEFAULT_TIMEOUT,
    ServiceUnavailableError,
    get_client,
    handle_response,
)

logger = logging.getLogger(__name__)


def is_reserved_ip(ioc: str) -> bool:
    """True for any address that isn't globally routable (private, loopback, link-local,
    CGNAT, multicast, documentation/benchmark ranges). Unparseable input counts as reserved,
    so it never leaves the backend either."""
    try:
        return not ipaddress.ip_address(ioc.strip()).is_global
    except ValueError:
        return True


IP_GEO_FIELDS = ("country", "region", "city", "lat", "lon", "timezone", "asn", "company")


async def check_ip_geo(ioc: str) -> dict[str, Any]:
    """Country/region/city, coordinates, ASN and owning company for a public IP from ipapi.is's
    keyless HTTPS tier (about 1,000 requests a day). Its `asn` is one string, "AS13335
    Cloudflare, Inc.", passed through as is."""
    if is_reserved_ip(ioc):
        return {"ip": ioc, "reserved": True, **dict.fromkeys(IP_GEO_FIELDS)}

    logger.debug("Checking IP %s with ipapi.is", ioc)
    client = get_client()
    response = await client.get(url="https://api.ipapi.is/", params={"q": ioc})
    result = await handle_response("ipapi.is", response)
    require_fields(result, ("is_bogon", *IP_GEO_FIELDS), label="ipapi.is")
    geo = {field: result[field] for field in IP_GEO_FIELDS}
    return {"ip": ioc, "reserved": bool(result["is_bogon"]), **geo}


RDAP_BOOTSTRAP = "https://rdap.org/ip/"
_RDAP_HEADERS = {"Accept": "application/rdap+json, application/json"}

IP_RDAP_FIELDS = (
    "handle",
    "name",
    "type",
    "start_address",
    "end_address",
    "cidrs",
    "country",
    "registrant",
    "abuse_emails",
    "registration",
    "last_changed",
    "registry",
    "registry_server",
)

# The RDAP server that answered -> the regional registry it belongs to, for the card's headline.
RIR_BY_RDAP_HOST = {
    "rdap.arin.net": "ARIN",
    "rdap.db.ripe.net": "RIPE NCC",
    "rdap.apnic.net": "APNIC",
    "rdap.lacnic.net": "LACNIC",
    "rdap.afrinic.net": "AFRINIC",
}


def _empty_rdap(ioc: str, *, reserved: bool, found: bool) -> dict[str, Any]:
    return {
        "ip": ioc,
        "reserved": reserved,
        "found": found,
        **dict.fromkeys(IP_RDAP_FIELDS),
        "cidrs": [],
        "abuse_emails": [],
    }


def _cidrs(raw: dict[str, Any]) -> list[str]:
    """RFC 9083 `cidr0_cidrs` extension (ARIN, RIPE, APNIC, LACNIC and AFRINIC all send it)."""
    cidrs = []
    for entry in raw.get("cidr0_cidrs") or []:
        prefix = entry.get("v4prefix") or entry.get("v6prefix")
        if prefix and entry.get("length") is not None:
            cidrs.append(f"{prefix}/{entry['length']}")
    return cidrs


def parse_ip_rdap(ioc: str, raw: Any, registry_server: str) -> dict[str, Any]:
    """Flatten an RDAP `ip network` object into the fields the card shows. The abuse contact is
    looked for at any depth: ARIN nests it under the registrant org, RIPE lists it top-level."""
    require_fields(raw, ("objectClassName",), label="RDAP")
    entities = extract_rdap_entities(raw)
    events = extract_rdap_events(raw)
    abuse_emails = sorted({e.email for e in entities if e.role == "abuse" and e.email})
    registrants = (e.organization or e.name for e in entities if e.role == "registrant")
    registrant = next((name for name in registrants if name), None)
    return {
        **_empty_rdap(ioc, reserved=False, found=True),
        "handle": raw.get("handle"),
        "name": raw.get("name"),
        "type": raw.get("type"),
        "start_address": raw.get("startAddress"),
        "end_address": raw.get("endAddress"),
        "cidrs": _cidrs(raw),
        "country": raw.get("country"),
        "registrant": registrant,
        "abuse_emails": abuse_emails,
        "registration": events.get("registration"),
        "last_changed": events.get("last changed"),
        "registry": RIR_BY_RDAP_HOST.get(registry_server),
        "registry_server": registry_server,
    }


async def check_ip_rdap(ioc: str) -> dict[str, Any]:
    """Netblock owner, range, registry and abuse contact for a public IP via the `rdap.org`
    bootstrap, which redirects to whichever RIR is authoritative (ARIN, RIPE, APNIC, LACNIC,
    AFRINIC). The redirect target isn't a fixed host, so every hop goes through `safe_get`.
    A 404 (unallocated space) is `found: false`, not an error."""
    if is_reserved_ip(ioc):
        return _empty_rdap(ioc, reserved=True, found=False)

    logger.debug("Checking IP %s with RDAP", ioc)
    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT, headers=_RDAP_HEADERS, follow_redirects=False
        ) as client:
            response = await safe_get(
                client,
                f"{RDAP_BOOTSTRAP}{ioc}",
                allow_private=settings.security.allow_private_network_targets,
            )
    except httpx.TimeoutException:
        raise  # the engine reports "RDAP request timed out"
    except (httpx.RequestError, SSRFValidationError) as exc:
        raise ServiceUnavailableError("RDAP", f"Could not reach RDAP: {exc}") from exc

    if response.status_code == 404:
        return _empty_rdap(ioc, reserved=False, found=False)
    raw = await handle_response("RDAP", response)
    # `safe_get` pins the connection to a vetted IP and puts the real hostname in the Host
    # header, so the registry that answered is read from there, not from `response.url`.
    return parse_ip_rdap(ioc, raw, response.request.headers.get("host", "unknown"))
