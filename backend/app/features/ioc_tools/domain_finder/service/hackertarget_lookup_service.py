"""
HackerTarget hostsearch business logic: turns raw hostname/IP pairs into a
deduplicated subdomain list, mirroring domain_finder's existing CT-log
subdomain-enumeration shape (`ct_subdomains_service.py`).
"""

import logging

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    HackerTargetHost,
    HackerTargetSubdomainsRequest,
    HackerTargetSubdomainsResponse,
)
from app.features.ioc_tools.domain_finder.service.hackertarget_api_service import (
    fetch_hackertarget_hosts,
)

logger = logging.getLogger(__name__)


async def perform_hackertarget_lookup(
    hackertarget_request: HackerTargetSubdomainsRequest,
) -> HackerTargetSubdomainsResponse:
    """
    Enumerate subdomains for a domain via HackerTarget's hostsearch API.

    Args:
        hackertarget_request: Validated HackerTarget subdomains request

    Returns:
        HackerTargetSubdomainsResponse containing a deduplicated subdomain list and raw hosts

    Raises:
        AppHTTPException: When the HackerTarget request fails
    """
    domain = hackertarget_request.domain
    logger.info("Starting HackerTarget subdomain enumeration for: %s", domain)

    raw_hosts = await fetch_hackertarget_hosts(domain)

    subdomains: set[str] = set()
    hosts: list[HackerTargetHost] = []
    for hostname, ip in raw_hosts:
        normalized = hostname.lower()
        # HackerTarget occasionally returns hosts unrelated to the queried domain
        # for a near-miss query, so only keep names that actually belong to it
        if normalized == domain or normalized.endswith(f".{domain}"):
            subdomains.add(normalized)
        hosts.append(HackerTargetHost(hostname=hostname, ip_address=ip))

    response = HackerTargetSubdomainsResponse(
        domain=domain,
        subdomains=sorted(subdomains),
        hosts=hosts,
        total_hosts=len(hosts),
    )

    logger.info(
        "HackerTarget subdomain enumeration completed for %s - %s unique subdomains from %s hosts",
        domain,
        len(subdomains),
        len(hosts),
    )
    return response
