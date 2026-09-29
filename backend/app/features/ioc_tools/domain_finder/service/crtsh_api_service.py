"""
Certificate Transparency log lookup via crt.sh's JSON endpoint.

crt.sh (run by Sectigo) mirrors public CT logs and needs no API key. A
`%.<domain>` wildcard query returns every certificate issued for the domain
and its subdomains, which doubles as a subdomain-enumeration source: SAN
entries on those certs commonly include hosts an operator never intended to
advertise.
"""

import logging
from typing import Any

import httpx

from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

CRTSH = Provider(name="crt.sh", code="CRTSH", base_url="https://crt.sh/")


async def fetch_crtsh_certificates(domain: str) -> list[dict[str, Any]]:
    """Raw Certificate Transparency log entries for a domain (and its subdomains) from crt.sh.
    Failures raise `AppHTTPException` (`provider_http`); crt.sh serves an HTML error page
    (not JSON) when overloaded or the query is malformed -> `CRTSH_INVALID_RESPONSE`."""

    def parse(response: httpx.Response) -> list[dict[str, Any]]:
        if not response.content:
            logger.info("crt.sh returned an empty response for domain: %s", domain)
            return []
        data = response.json()
        logger.info(
            "Retrieved %s certificate entries from crt.sh for domain: %s", len(data), domain
        )
        return data

    return await provider_get(
        CRTSH, subject=domain, params={"q": f"%.{domain}", "output": "json"}, parse=parse
    )
