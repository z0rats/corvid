"""Censys Platform API v3 lookups with a free-tier Personal Access Token.

The free tier only gets the Lookup endpoints (`/v3/global/asset/...`); search needs a paid
organization and isn't used. No `organization_id` is sent, so requests draw on the account's
free wallet. Responses are trimmed to what the card shows: a raw host carries every service's
full banner and protocol detail, far too much to keep in lookup history.

Censys omits a field it has nothing for (no services, no software), so an absent list is
"nothing found". A present field of the wrong type, a host without `ip`, a web property without
`hostname`, or a host whose `service_count` says services exist while `services` is missing is
drift (ADR 0022).
"""

import logging
from typing import Any

import httpx

from app.core.external_sources.contract import SourceDriftError, require_dict, require_fields

from .client_base import (
    ServiceAuthError,
    ServiceError,
    _require_apikey,
    get_client,
    handle_response,
)
from .ip_context_clients import is_reserved_ip

logger = logging.getLogger(__name__)

CENSYS = "Censys"
CENSYS_API = "https://api.platform.censys.io/v3/global/asset"
# A domain is looked up as a web property `<hostname>:<port>`; HTTPS first.
WEBPROPERTY_PORTS = (443, 80)


def _raise_for_censys_status(response: httpx.Response) -> None:
    """Turn the two errors a user can act on into a message saying what to do. Everything
    else (429, 5xx, ...) falls through to `handle_response`'s generic mapping."""
    if response.status_code == 401:
        raise ServiceAuthError(
            CENSYS,
            "Censys rejected the Personal Access Token. Create a new one under API Access "
            "on platform.censys.io and save it in Settings → API Keys.",
        )
    if response.status_code == 403 and "organization" in response.text.lower():
        raise ServiceError(
            CENSYS, "This Censys endpoint needs a paid organization, not the free tier.", 403
        )


async def _get_resource(path: str, apikey: str) -> dict[str, Any] | None:
    """`result.resource` of one lookup, or None for a 404 (Censys has no such asset)."""
    response = await get_client().get(
        url=f"{CENSYS_API}/{path}",
        headers={"Authorization": f"Bearer {apikey}", "Accept": "application/json"},
    )
    if response.status_code == 404:
        return None
    _raise_for_censys_status(response)
    body = await handle_response(CENSYS, response)
    result = require_fields(body, ("result",), label=CENSYS)["result"]
    resource = require_fields(result, ("resource",), label=CENSYS)["resource"]
    return require_dict(resource, label=CENSYS, where="result.resource")


def _optional(resource: dict[str, Any], field: str, kind: type) -> Any:
    """`resource[field]` if present, else an empty `kind`; a present value of another type is
    drift. Censys leaves out a field it has no data for, so absence alone means "none"."""
    value = resource.get(field)
    if value is None:
        return kind()
    if not isinstance(value, kind):
        raise SourceDriftError(
            f"{CENSYS}: response schema changed - '{field}' is not a {kind.__name__}"
        )
    return value


def _cert_summary(cert: Any) -> dict[str, Any] | None:
    if not isinstance(cert, dict):
        return None
    parsed = cert.get("parsed") or {}
    return {
        "subject_dn": parsed.get("subject_dn"),
        "issuer_dn": parsed.get("issuer_dn"),
        "fingerprint_sha256": cert.get("fingerprint_sha256"),
        "names": cert.get("names") or [],
    }


def summarize_host(ip: str, resource: dict[str, Any] | None) -> dict[str, Any]:
    if resource is None:
        return {
            "kind": "host",
            "reserved": False,
            "not_found": True,
            "ip": ip,
            "services": [],
            "hostnames": [],
        }
    require_fields(resource, ("ip",), label=CENSYS, where="host")
    raw_services = _optional(resource, "services", list)
    service_count = resource.get("service_count")
    if isinstance(service_count, int) and service_count > 0 and not raw_services:
        raise SourceDriftError(
            f"{CENSYS}: response schema changed - service_count={service_count} but no 'services'"
        )
    location = _optional(resource, "location", dict)
    routing = _optional(resource, "autonomous_system", dict)
    services = [
        {
            "port": service.get("port"),
            "protocol": service.get("protocol"),
            "transport_protocol": service.get("transport_protocol"),
            "scan_time": service.get("scan_time"),
            "cert": _cert_summary(service.get("cert")),
        }
        for service in raw_services
        if isinstance(service, dict)
    ]
    return {
        "kind": "host",
        "reserved": False,
        "not_found": False,
        "ip": resource["ip"],
        "service_count": service_count if isinstance(service_count, int) else len(services),
        "services": sorted(services, key=lambda s: (s["port"] is None, s["port"] or 0)),
        "hostnames": _optional(resource, "dns", dict).get("names") or [],
        "location": {
            "country": location.get("country"),
            "country_code": location.get("country_code"),
            "city": location.get("city"),
        },
        "autonomous_system": {
            "asn": routing.get("asn"),
            "name": routing.get("name"),
            "bgp_prefix": routing.get("bgp_prefix"),
        },
    }


def summarize_webproperty(hostname: str, resource: dict[str, Any] | None) -> dict[str, Any]:
    if resource is None:
        return {
            "kind": "webproperty",
            "reserved": False,
            "not_found": True,
            "hostname": hostname,
            "software": [],
        }
    require_fields(resource, ("hostname",), label=CENSYS, where="web property")
    software = [
        {
            "vendor": item.get("vendor"),
            "product": item.get("product"),
            "version": item.get("version"),
            # Censys' own classification, e.g. a WAF or CDN; the card highlights a WAF.
            "types": item.get("type") or [],
        }
        for item in _optional(resource, "software", list)
        if isinstance(item, dict) and (item.get("product") or item.get("vendor"))
    ]
    return {
        "kind": "webproperty",
        "reserved": False,
        "not_found": False,
        "hostname": resource["hostname"],
        "port": resource.get("port"),
        "scan_time": resource.get("scan_time"),
        "software": software,
        "cert": _cert_summary(resource.get("cert")),
    }


async def check_censys(ioc: str, asset: str, apikey: str) -> dict[str, Any]:
    """Censys services per port (IP) or software stack + certificate (domain, as the web
    property on 443, falling back to 80, so a domain Censys doesn't know costs two lookups). An
    asset Censys doesn't know is `not_found`, not an error. A private or reserved IP is never
    sent (`reserved: true`), as with the keyless IP providers."""
    _require_apikey(CENSYS, apikey)

    if asset == "host":
        if is_reserved_ip(ioc):
            return {**summarize_host(ioc, None), "reserved": True}
        logger.debug("Checking host %s with Censys", ioc)
        return summarize_host(ioc, await _get_resource(f"host/{ioc}", apikey))

    logger.debug("Checking web property %s with Censys", ioc)
    for port in WEBPROPERTY_PORTS:
        resource = await _get_resource(f"webproperty/{ioc}:{port}", apikey)
        if resource is not None:
            return summarize_webproperty(ioc, resource)
    return summarize_webproperty(ioc, None)
