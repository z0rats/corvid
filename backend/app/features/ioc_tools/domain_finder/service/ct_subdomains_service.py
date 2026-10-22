"""
Certificate Transparency subdomain enumeration business logic: merges crt.sh's raw log entries
and Cert Spotter's issuances into one deduplicated subdomain list plus a per-source status, for
feeding domain_finder's existing typosquat/phishing discovery flow with a subdomain list to also
scan.

The two sources are queried concurrently and either one answering is enough: crt.sh is often
overloaded, which is why Cert Spotter is there at all. A failed source is reported in `sources`
as not checked; only when both fail does the lookup itself fail.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    CtCertificate,
    CtSourceStatus,
    CtSubdomainsRequest,
    CtSubdomainsResponse,
)
from app.features.ioc_tools.domain_finder.service.certspotter_api_service import (
    CERTSPOTTER,
    CertSpotterPage,
    fetch_certspotter_issuances,
)
from app.features.ioc_tools.domain_finder.service.crtsh_api_service import (
    CRTSH,
    fetch_crtsh_certificates,
)
from app.features.ioc_tools.domain_finder.utils.subdomain_utils import subdomains_of

logger = logging.getLogger(__name__)

# Turns one source's successful answer into its subdomains and status line.
type SourceReader = Callable[[Any, str], tuple[set[str], CtSourceStatus]]


async def perform_ct_subdomains_lookup(ct_request: CtSubdomainsRequest) -> CtSubdomainsResponse:
    """
    Enumerate subdomains for a domain via Certificate Transparency logs (crt.sh + Cert Spotter).

    Args:
        ct_request: Validated CT subdomains request containing the domain to search

    Returns:
        CtSubdomainsResponse with the merged subdomain list, per-source status and crt.sh's
        per-certificate detail

    Raises:
        AppHTTPException: When every CT source fails (`CT_ALL_SOURCES_FAILED`)
    """
    domain = ct_request.domain
    logger.info("Starting CT subdomain enumeration for: %s", domain)

    crtsh_result, certspotter_result = await asyncio.gather(
        fetch_crtsh_certificates(domain),
        fetch_certspotter_issuances(domain),
        return_exceptions=True,
    )
    _reraise_unexpected(crtsh_result, certspotter_result)

    # crt.sh's per-certificate detail is kept as-is; only its subdomains merge with Cert Spotter's.
    certificates = (
        [] if isinstance(crtsh_result, AppHTTPException) else _crtsh_certificates(crtsh_result)
    )
    outcomes: list[tuple[str, Any, SourceReader]] = [
        (CRTSH.name, crtsh_result, _crtsh_answer),
        (CERTSPOTTER.name, certspotter_result, _certspotter_answer),
    ]

    subdomains: set[str] = set()
    sources: list[CtSourceStatus] = []
    for name, result, read in outcomes:
        if isinstance(result, AppHTTPException):
            sources.append(_failed(name, result))
            continue
        names, status = read(result, domain)
        subdomains |= names
        sources.append(status)

    if not any(source.ok for source in sources):
        raise AppHTTPException(
            status_code=502,
            detail="; ".join(f"{s.name}: {s.error} ({s.error_code})" for s in sources),
            error_code="CT_ALL_SOURCES_FAILED",
        )

    response = CtSubdomainsResponse(
        domain=domain,
        subdomains=sorted(subdomains),
        sources=sources,
        certificates=certificates,
        total_certificates=len(certificates),
    )

    logger.info(
        "CT subdomain enumeration completed for %s - %s unique subdomains (%s)",
        domain,
        len(subdomains),
        ", ".join(f"{s.name}: {s.subdomain_count if s.ok else s.error_code}" for s in sources),
    )
    return response


def _reraise_unexpected(*results: object) -> None:
    """`provider_get` maps every failure onto an `AppHTTPException`; anything else is a bug."""
    for result in results:
        if isinstance(result, BaseException) and not isinstance(result, AppHTTPException):
            raise result


def _failed(name: str, exc: AppHTTPException) -> CtSourceStatus:
    logger.warning("CT source %s failed: %s", name, exc.error_code)
    return CtSourceStatus(name=name, ok=False, error=exc.detail, error_code=exc.error_code)


def _crtsh_answer(entries: list[dict], domain: str) -> tuple[set[str], CtSourceStatus]:
    names: set[str] = set()
    for entry in entries:
        names |= subdomains_of((entry.get("name_value") or "").split("\n"), domain)
    status = CtSourceStatus(
        name=CRTSH.name, ok=True, subdomain_count=len(names), certificate_count=len(entries)
    )
    return names, status


def _certspotter_answer(page: CertSpotterPage, domain: str) -> tuple[set[str], CtSourceStatus]:
    names: set[str] = set()
    for issuance in page.issuances:
        names |= subdomains_of(issuance["dns_names"], domain)
    status = CtSourceStatus(
        name=CERTSPOTTER.name,
        ok=True,
        subdomain_count=len(names),
        certificate_count=len(page.issuances),
        truncated=page.truncated,
    )
    return names, status


def _crtsh_certificates(entries: list[dict]) -> list[CtCertificate]:
    return [
        CtCertificate(
            id=entry.get("id"),
            issuer_name=entry.get("issuer_name"),
            common_name=entry.get("common_name"),
            name_value=entry.get("name_value") or "",
            not_before=_parse_crtsh_date(entry.get("not_before")),
            not_after=_parse_crtsh_date(entry.get("not_after")),
        )
        for entry in entries
    ]


def _parse_crtsh_date(date_str: str | None) -> datetime | None:
    """Parse a crt.sh date string (ISO 8601, no timezone suffix) into a datetime"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Could not parse crt.sh date: %s", date_str)
        return None
