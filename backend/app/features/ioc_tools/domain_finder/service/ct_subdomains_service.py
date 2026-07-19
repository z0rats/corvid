"""
Certificate Transparency subdomain enumeration business logic: turns crt.sh's
raw log entries into a deduplicated subdomain list plus per-certificate
detail, for feeding domain_finder's existing typosquat/phishing discovery
flow with a subdomain list to also scan.
"""
import logging
from datetime import datetime

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    CtCertificate,
    CtSubdomainsRequest,
    CtSubdomainsResponse,
)
from app.features.ioc_tools.domain_finder.service.crtsh_api_service import fetch_crtsh_certificates

logger = logging.getLogger(__name__)


async def perform_ct_subdomains_lookup(ct_request: CtSubdomainsRequest) -> CtSubdomainsResponse:
    """
    Enumerate subdomains for a domain via crt.sh Certificate Transparency logs.

    Args:
        ct_request: Validated CT subdomains request containing the domain to search

    Returns:
        CtSubdomainsResponse containing a deduplicated subdomain list and per-certificate detail

    Raises:
        AppHTTPException: When the crt.sh request fails
    """
    domain = ct_request.domain
    logger.info("Starting CT subdomain enumeration for: %s", domain)

    raw_entries = await fetch_crtsh_certificates(domain)

    subdomains: set[str] = set()
    certificates: list[CtCertificate] = []

    for entry in raw_entries:
        name_value = entry.get("name_value") or ""
        # A multi-domain (SAN) cert's name_value can include hosts unrelated to the
        # queried domain, so only keep names that actually belong to it
        names = {name.strip().lower().lstrip("*.") for name in name_value.split("\n") if name.strip()}
        names = {name for name in names if name == domain or name.endswith(f".{domain}")}
        subdomains.update(names)

        certificates.append(CtCertificate(
            id=entry.get("id"),
            issuer_name=entry.get("issuer_name"),
            common_name=entry.get("common_name"),
            name_value=name_value,
            not_before=_parse_crtsh_date(entry.get("not_before")),
            not_after=_parse_crtsh_date(entry.get("not_after")),
        ))

    response = CtSubdomainsResponse(
        domain=domain,
        subdomains=sorted(subdomains),
        certificates=certificates,
        total_certificates=len(certificates),
    )

    logger.info(
        "CT subdomain enumeration completed for %s - %s unique subdomains from %s certificate entries",
        domain, len(subdomains), len(certificates),
    )
    return response


def _parse_crtsh_date(date_str: str | None) -> datetime | None:
    """Parse a crt.sh date string (ISO 8601, no timezone suffix) into a datetime"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Could not parse crt.sh date: %s", date_str)
        return None
