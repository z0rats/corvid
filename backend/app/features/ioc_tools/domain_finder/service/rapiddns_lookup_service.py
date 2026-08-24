"""
RapidDNS business logic: turns raw (hostname, record_type, address) rows into
a deduplicated subdomain list, mirroring domain_finder's existing CT-log/
HackerTarget subdomain-enumeration shape.
"""

import logging

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    RapidDnsRecord,
    RapidDnsSubdomainsRequest,
    RapidDnsSubdomainsResponse,
)
from app.features.ioc_tools.domain_finder.service.rapiddns_api_service import (
    fetch_rapiddns_records,
)

logger = logging.getLogger(__name__)


async def perform_rapiddns_lookup(
    rapiddns_request: RapidDnsSubdomainsRequest,
) -> RapidDnsSubdomainsResponse:
    """
    Enumerate subdomains for a domain via RapidDNS's subdomain lookup page.

    Args:
        rapiddns_request: Validated RapidDNS subdomains request

    Returns:
        RapidDnsSubdomainsResponse containing a deduplicated subdomain list and raw records

    Raises:
        AppHTTPException: When the RapidDNS request fails
    """
    domain = rapiddns_request.domain
    logger.info("Starting RapidDNS subdomain enumeration for: %s", domain)

    raw_records = await fetch_rapiddns_records(domain)

    subdomains: set[str] = set()
    records: list[RapidDnsRecord] = []
    for hostname, record_type, address in raw_records:
        normalized = hostname.lower()
        # RapidDNS's table can include hosts unrelated to the queried domain
        # (e.g. same-IP entries), so only count names that actually belong to it
        if normalized == domain or normalized.endswith(f".{domain}"):
            subdomains.add(normalized)
        records.append(RapidDnsRecord(hostname=hostname, record_type=record_type, address=address))

    response = RapidDnsSubdomainsResponse(
        domain=domain,
        subdomains=sorted(subdomains),
        records=records,
        total_records=len(records),
    )

    logger.info(
        "RapidDNS subdomain enumeration completed for %s - %s unique subdomains from %s records",
        domain,
        len(subdomains),
        len(records),
    )
    return response
