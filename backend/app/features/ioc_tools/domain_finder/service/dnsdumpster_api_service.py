"""
DNSDumpster API client for domain reconnaissance.

DNSDumpster's official API (https://dnsdumpster.com/developer/) needs an API key
(X-API-Key header) - unlike its sibling crt.sh/RDAP panels, there's no keyless
fallback. Free tier caps a domain lookup at 50 records and rate-limits to
1 request/2s.
"""

import logging
from typing import Any

import httpx

from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

DNSDUMPSTER = Provider(
    name="DNSDumpster", code="DNSDUMPSTER", base_url="https://api.dnsdumpster.com"
)


async def fetch_dnsdumpster_data(domain: str, api_key: str) -> dict[str, Any]:
    """Raw DNSDumpster domain-lookup response. Failures raise `AppHTTPException`
    (`provider_http`), plus `DNSDUMPSTER_INVALID_KEY` for a rejected key and
    `DNSDUMPSTER_RATE_LIMITED` for a rate-limit hit."""

    def check(response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            logger.warning(
                "DNSDumpster rejected the configured API key (status %s)", response.status_code
            )
            raise DNSDUMPSTER.error(
                401, "INVALID_KEY", "DNSDumpster rejected the configured API key"
            )
        if response.status_code == 429:
            logger.warning("DNSDumpster rate limit exceeded for domain: %s", domain)
            raise DNSDUMPSTER.error(
                429, "RATE_LIMITED", "DNSDumpster API rate limit exceeded, try again shortly"
            )

    def parse(response: httpx.Response) -> dict[str, Any]:
        data = response.json()
        logger.info("Retrieved DNSDumpster data for domain: %s", domain)
        return data

    return await provider_get(
        DNSDUMPSTER,
        f"/domain/{domain}",
        subject=domain,
        headers={"X-API-Key": api_key},
        check=check,
        parse=parse,
    )
