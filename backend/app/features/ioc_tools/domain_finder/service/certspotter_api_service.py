"""
Certificate Transparency issuances via SSLMate's Cert Spotter API.

A second CT source next to crt.sh, which is often overloaded: keyless, but the unauthenticated
tier allows only a handful of queries per hour, so one lookup reads exactly one page (about 80
issuances, newest certificates only) and reports whether more exist rather than paging on.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.external_sources.contract import SourceDriftError, require_fields
from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

CERTSPOTTER = Provider(
    name="Cert Spotter", code="CERTSPOTTER", base_url="https://api.certspotter.com/v1/"
)

# What `ct_subdomains_service` reads from every issuance.
ISSUANCE_FIELDS = ("id", "dns_names")


@dataclass(frozen=True)
class CertSpotterPage:
    issuances: list[dict[str, Any]]
    # Cert Spotter has more issuances than the one page read (a `Link: rel="next"` header).
    truncated: bool = False


def _check(response: httpx.Response) -> None:
    if response.status_code == 429:
        raise CERTSPOTTER.error(
            429, "RATE_LIMITED", "Cert Spotter's hourly keyless quota is used up, try again later"
        )


async def fetch_certspotter_issuances(domain: str) -> CertSpotterPage:
    """One page of CT issuances for a domain and its subdomains from Cert Spotter. Failures raise
    `AppHTTPException` (`provider_http`), plus `CERTSPOTTER_RATE_LIMITED` once the keyless quota
    is used up; JSON that isn't a list of issuances carrying a `dns_names` list of strings ->
    `CERTSPOTTER_SCHEMA_DRIFT`. `[]` is a domain with no current certificates."""

    def parse(response: httpx.Response) -> CertSpotterPage:
        data = response.json()
        if not isinstance(data, list):
            raise SourceDriftError(f"{CERTSPOTTER.name}: response is not a JSON array")
        for issuance in data:
            require_fields(issuance, ISSUANCE_FIELDS, label=CERTSPOTTER.name, where="issuance")
            names = issuance["dns_names"]
            if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
                raise SourceDriftError(f"{CERTSPOTTER.name}: `dns_names` is not a list of names")
        truncated = "next" in response.links
        logger.info(
            "Retrieved %s issuances from Cert Spotter for domain: %s (truncated=%s)",
            len(data),
            domain,
            truncated,
        )
        return CertSpotterPage(issuances=data, truncated=truncated)

    return await provider_get(
        CERTSPOTTER,
        "issuances",
        subject=domain,
        params={"domain": domain, "include_subdomains": "true", "expand": "dns_names"},
        parse=parse,
        check=_check,
    )
