"""
RDAP (Registration Data Access Protocol) client for WHOIS-style domain lookups.

RDAP is the IETF-standardized, structured-JSON successor to plain-text WHOIS and
needs no API key. `rdap.org` (operated by APNIC Labs, endorsed by IANA as a public
bootstrap service) resolves a domain to its authoritative registry RDAP server via
an HTTP redirect, so a single fixed entrypoint covers every TLD without this app
having to maintain its own IANA bootstrap-registry mapping.
"""

import logging
from typing import Any

import httpx

from app.core.config.settings import settings
from app.core.security.ssrf_guard import safe_get
from app.features.ioc_tools.domain_finder.service.provider_http import (
    USER_AGENT,
    Provider,
    provider_errors,
)

logger = logging.getLogger(__name__)

# Not fetched via `provider_get`: rdap.org answers with a redirect to whichever registry
# server is authoritative, so the host actually contacted isn't fixed - it goes through
# `safe_get`, and only the error mapping is shared.
RDAP = Provider(
    name="RDAP",
    code="RDAP",
    base_url="https://rdap.org/domain/",
    timeout=15.0,
    accept="application/rdap+json, application/json",
)


async def fetch_rdap_domain_data(domain: str) -> tuple[dict[str, Any], str]:
    """RDAP registration data for a domain, following the rdap.org bootstrap redirect:
    `(raw RDAP response, the authoritative RDAP server host that answered)`. Failures raise
    `AppHTTPException` (`provider_http`), plus `RDAP_NOT_FOUND` for an unknown domain/TLD."""
    url = f"{RDAP.base_url}{domain}"
    logger.debug("Fetching RDAP data from bootstrap: %s", url)

    async with provider_errors(RDAP, domain):
        async with httpx.AsyncClient(
            timeout=RDAP.timeout,
            headers={"User-Agent": USER_AGENT, "Accept": RDAP.accept or "application/json"},
            follow_redirects=False,
        ) as client:
            response = await safe_get(
                client, url, allow_private=settings.security.allow_private_network_targets
            )

            if response.status_code == 404:
                raise RDAP.error(404, "NOT_FOUND", f"No RDAP record found for domain: {domain}")

            response.raise_for_status()
            data = response.json()
            # `safe_get` pins the connection to a validated IP and rewrites the request's
            # Host header to the real hostname, so recover the authoritative server from
            # there rather than from `response.url` (which holds the pinned IP instead).
            rdap_server = response.request.headers.get("host", "unknown")
            logger.info("RDAP lookup succeeded for %s via %s", domain, rdap_server)
            return data, rdap_server
