"""Domain lookup API routes"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, Request, status
from pydantic import BaseModel

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    BlocklistRequest,
    BlocklistResponse,
    CtSubdomainsRequest,
    CtSubdomainsResponse,
    DnsDumpsterRequest,
    DnsDumpsterResponse,
    DnsLookupRequest,
    DnsLookupResponse,
    DnssecRequest,
    DnssecResponse,
    DomainLookupRequest,
    DomainLookupResponse,
    HackerTargetSubdomainsRequest,
    HackerTargetSubdomainsResponse,
    HostProbeRequest,
    HostProbeResponse,
    RapidDnsSubdomainsRequest,
    RapidDnsSubdomainsResponse,
    SecurityHeadersRequest,
    SecurityHeadersResponse,
    SiteCrawlRequest,
    SiteCrawlResponse,
    SslInfoRequest,
    SslInfoResponse,
    SubfinderSubdomainsRequest,
    SubfinderSubdomainsResponse,
    TemporalAnalysisRequest,
    TemporalAnalysisResponse,
    WaybackLookupRequest,
    WaybackLookupResponse,
    WhoisLookupRequest,
    WhoisLookupResponse,
)
from app.features.ioc_tools.domain_finder.service.blocklist_service import perform_blocklist_check
from app.features.ioc_tools.domain_finder.service.ct_subdomains_service import (
    perform_ct_subdomains_lookup,
)
from app.features.ioc_tools.domain_finder.service.dns_lookup_service import perform_dns_lookup
from app.features.ioc_tools.domain_finder.service.dnsdumpster_service import (
    perform_dnsdumpster_lookup,
)
from app.features.ioc_tools.domain_finder.service.dnssec_service import perform_dnssec_lookup
from app.features.ioc_tools.domain_finder.service.domain_lookup_service import perform_domain_lookup
from app.features.ioc_tools.domain_finder.service.hackertarget_lookup_service import (
    perform_hackertarget_lookup,
)
from app.features.ioc_tools.domain_finder.service.host_probe_service import (
    get_httpx_version,
    is_httpx_available,
    perform_host_probe,
)
from app.features.ioc_tools.domain_finder.service.rapiddns_lookup_service import (
    perform_rapiddns_lookup,
)
from app.features.ioc_tools.domain_finder.service.security_headers_service import (
    perform_security_headers_lookup,
)
from app.features.ioc_tools.domain_finder.service.site_crawler_service import perform_site_crawl
from app.features.ioc_tools.domain_finder.service.ssl_info_service import perform_ssl_info_lookup
from app.features.ioc_tools.domain_finder.service.subfinder_service import (
    get_subfinder_version,
    is_subfinder_available,
    perform_subfinder_lookup,
)
from app.features.ioc_tools.domain_finder.service.temporal_analysis_service import (
    perform_temporal_analysis,
)
from app.features.ioc_tools.domain_finder.service.wayback_lookup_service import (
    perform_wayback_lookup,
)
from app.features.ioc_tools.domain_finder.service.whois_lookup_service import perform_whois_lookup

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/domain", tags=["Domain Lookup"])


def _add_panel_routes(
    path: str,
    *,
    name: str,
    request_model: type[BaseModel],
    response_model: type[BaseModel],
    service: Callable[..., Awaitable[Any]],
    summary: str,
    description: str,
    limit: str = "30/minute",
    with_db: bool = False,
) -> None:
    """Mount one panel's `POST {path}` (JSON body) + `GET {path}/{domain}` pair - both build
    `request_model` (its validator normalizes the domain) and return `service(request)`
    (`service(request, db)` when `with_db`). `service` is called through a lambda so it's
    resolved at request time, not bound here. Each endpoint gets its own `__name__` before
    `limiter.limit` wraps it, since slowapi keys its per-route counters by function name."""

    async def run(panel_request: Any, db: Any, method: str) -> Any:
        logger.info("%s %s request - Domain: %s", method, path, panel_request.domain)
        extra = (db,) if with_db else ()
        result = await service(panel_request, *extra)
        logger.info("%s %s completed - Domain: %s", method, path, panel_request.domain)
        return result

    if with_db:

        async def post_endpoint(request: Request, body: request_model, db: ReadSessionDep):  # type: ignore[valid-type]
            return await run(body, db, "POST")

        async def get_endpoint(request: Request, domain: str, db: ReadSessionDep):
            return await run(request_model(domain=domain), db, "GET")

    else:

        async def post_endpoint(request: Request, body: request_model):  # type: ignore[valid-type,misc]
            return await run(body, None, "POST")

        async def get_endpoint(request: Request, domain: str):  # type: ignore[misc]
            return await run(request_model(domain=domain), None, "GET")

    for endpoint, suffix in ((post_endpoint, "post"), (get_endpoint, "get")):
        endpoint.__name__ = endpoint.__qualname__ = f"{name}_{suffix}"

    router.post(
        path,
        response_model=response_model,
        status_code=status.HTTP_200_OK,
        summary=summary,
        description=description,
    )(limiter.limit(limit)(post_endpoint))
    router.get(
        f"{path}/{{domain}}",
        response_model=response_model,
        status_code=status.HTTP_200_OK,
        summary=f"{summary} via URL parameter",
        description=f"{description} (domain taken from the URL path)",
    )(limiter.limit(limit)(get_endpoint))


_add_panel_routes(
    "/lookup",
    name="lookup_domain",
    request_model=DomainLookupRequest,
    response_model=DomainLookupResponse,
    service=lambda *args: perform_domain_lookup(*args),
    summary="Perform domain lookup using URLScan.io",
    description=(
        "Lookup domain information using the URLScan.io API to find scan "
        "results and security information"
    ),
)

_add_panel_routes(
    "/whois",
    name="whois_lookup",
    request_model=WhoisLookupRequest,
    response_model=WhoisLookupResponse,
    service=lambda *args: perform_whois_lookup(*args),
    summary="Perform WHOIS lookup via RDAP",
    description=(
        "Look up domain registration data (registrar, creation/expiry/updated "
        "dates, registrant org, nameservers) via RDAP"
    ),
)

_add_panel_routes(
    "/ct-subdomains",
    name="ct_subdomains_lookup",
    request_model=CtSubdomainsRequest,
    response_model=CtSubdomainsResponse,
    service=lambda *args: perform_ct_subdomains_lookup(*args),
    summary="Enumerate subdomains via Certificate Transparency logs",
    description=(
        "Query crt.sh's Certificate Transparency log mirror to enumerate "
        "subdomains and cert issuance history for a domain"
    ),
)

_add_panel_routes(
    "/hackertarget-subdomains",
    name="hackertarget_subdomains_lookup",
    request_model=HackerTargetSubdomainsRequest,
    response_model=HackerTargetSubdomainsResponse,
    service=lambda *args: perform_hackertarget_lookup(*args),
    summary="Enumerate subdomains via HackerTarget's hostsearch API",
    description=(
        "Query HackerTarget's free hostsearch API to enumerate subdomains and their "
        "resolved IPs for a domain"
    ),
)

_add_panel_routes(
    "/rapiddns-subdomains",
    name="rapiddns_subdomains_lookup",
    request_model=RapidDnsSubdomainsRequest,
    response_model=RapidDnsSubdomainsResponse,
    service=lambda *args: perform_rapiddns_lookup(*args),
    summary="Enumerate subdomains via RapidDNS",
    description=(
        "Query RapidDNS's public subdomain lookup page to enumerate subdomains and their "
        "DNS records for a domain"
    ),
)

_add_panel_routes(
    "/subfinder-subdomains",
    name="subfinder_subdomains_lookup",
    request_model=SubfinderSubdomainsRequest,
    response_model=SubfinderSubdomainsResponse,
    service=lambda *args: perform_subfinder_lookup(*args),
    summary="Enumerate subdomains via subfinder",
    description=(
        "Run subfinder (shelled out to as a subprocess) to passively enumerate subdomains "
        "across its ~55 built-in sources, using only keyless ones"
    ),
    limit="10/minute",  # heavier than other domain_finder checks: spawns a subprocess
)

_add_panel_routes(
    "/host-probe",
    name="host_probe",
    request_model=HostProbeRequest,
    response_model=HostProbeResponse,
    service=lambda *args: perform_host_probe(*args),
    summary="Probe a domain for a live http/https host via httpx",
    description=(
        "Run httpx (shelled out to as a subprocess) to detect which of http/https is live "
        "for a domain, along with title, server, detected technologies, favicon hash, and "
        "TLS certificate data - useful after subdomain enumeration to see which discovered "
        "hosts are worth a closer look"
    ),
    limit="10/minute",  # heavier than other domain_finder checks: spawns a subprocess
)

_add_panel_routes(
    "/ssl-info",
    name="ssl_info_lookup",
    request_model=SslInfoRequest,
    response_model=SslInfoResponse,
    service=lambda *args: perform_ssl_info_lookup(*args),
    summary="Inspect a domain's TLS certificate",
    description=(
        "Connect to a domain on port 443 and parse the TLS certificate it presents "
        "(subject, issuer, validity, SAN, hostname match) - certificate verification is "
        "deliberately skipped so self-signed/expired/mismatched certificates are still shown"
    ),
)

_add_panel_routes(
    "/security-headers",
    name="security_headers_lookup",
    request_model=SecurityHeadersRequest,
    response_model=SecurityHeadersResponse,
    service=lambda *args: perform_security_headers_lookup(*args),
    summary="Audit a domain's HTTPS security headers",
    description=(
        "Fetch a domain over HTTPS and check for baseline security response headers "
        "(HSTS, CSP, X-Frame-Options, etc.), with a dedicated HSTS directive parse"
    ),
)

_add_panel_routes(
    "/dnssec",
    name="dnssec_lookup",
    request_model=DnssecRequest,
    response_model=DnssecResponse,
    service=lambda *args: perform_dnssec_lookup(*args),
    summary="Check whether a domain publishes DNSSEC records",
    description="Check a domain for published DNSKEY/DS records as a quick DNSSEC signal",
)

_add_panel_routes(
    "/blocklist",
    name="blocklist_check",
    request_model=BlocklistRequest,
    response_model=BlocklistResponse,
    service=lambda *args: perform_blocklist_check(*args),
    summary="Check a domain against public DNS-filtering resolvers",
    description=(
        "Query a domain via several public providers' security-filtering DNS resolver and "
        "compare against that provider's plain resolver to detect DNS-level blocking/sinkholing"
    ),
)

_add_panel_routes(
    "/dns",
    name="dns_lookup",
    request_model=DnsLookupRequest,
    response_model=DnsLookupResponse,
    service=lambda *args: perform_dns_lookup(*args),
    summary="Perform DNS record lookup",
    description=(
        "Resolve A/AAAA/MX/TXT/NS/CNAME records for a domain, plus reverse DNS "
        "(PTR) for any resolved IPs"
    ),
)

_add_panel_routes(
    "/dnsdumpster",
    name="dnsdumpster_lookup",
    request_model=DnsDumpsterRequest,
    response_model=DnsDumpsterResponse,
    service=lambda *args: perform_dnsdumpster_lookup(*args),
    summary="Perform a DNSDumpster domain lookup",
    description=(
        "Look up DNS records, ASN/geo, reverse DNS, and HTTP(S) banners for a "
        "domain via the DNSDumpster API. Requires a DNSDumpster API key "
        "configured under Settings > API Keys."
    ),
    with_db=True,
)

_add_panel_routes(
    "/temporal-analysis",
    name="temporal_analysis",
    request_model=TemporalAnalysisRequest,
    response_model=TemporalAnalysisResponse,
    service=lambda *args: perform_temporal_analysis(*args),
    summary="Build an aggregated temporal-analysis timeline for a domain",
    description=(
        "Aggregate WHOIS registration/expiry dates, the live TLS certificate's validity "
        "window, Wayback Machine first/last capture, and the homepage's schema.org "
        "JSON-LD dates into one chronological timeline"
    ),
)


@router.post(
    "/wayback",
    response_model=WaybackLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Look up Wayback Machine capture history",
    description=(
        "Look up archived snapshots of a domain (or a specific page under it) via the "
        "Wayback Machine's CDX API"
    ),
)
@limiter.limit("30/minute")
async def wayback_lookup_post(
    request: Request, wayback_request: WaybackLookupRequest
) -> WaybackLookupResponse:
    """Perform a Wayback Machine lookup via POST request"""
    logger.info("POST Wayback lookup request - Domain: %s", wayback_request.domain)
    result = await perform_wayback_lookup(wayback_request)
    logger.info(
        "POST Wayback lookup completed - Domain: %s, Snapshots: %s",
        wayback_request.domain,
        result.total_snapshots,
    )
    return result


@router.get(
    "/wayback/{domain}",
    response_model=WaybackLookupResponse,
    status_code=status.HTTP_200_OK,
    summary="Look up Wayback Machine capture history via URL parameter",
    description=(
        "Query the Wayback Machine's CDX API using domain from URL path, optionally narrowed "
        "to a single page via the `path` query parameter"
    ),
)
@limiter.limit("30/minute")
async def wayback_lookup_get(
    request: Request, domain: str, path: str | None = None
) -> WaybackLookupResponse:
    """Perform a Wayback Machine lookup using domain from URL path via GET request"""
    logger.info("GET Wayback lookup request - Domain: %s, Path: %s", domain, path)
    wayback_request = WaybackLookupRequest(domain=domain, path=path)
    result = await perform_wayback_lookup(wayback_request)
    logger.info(
        "GET Wayback lookup completed - Domain: %s, Snapshots: %s", domain, result.total_snapshots
    )
    return result


@router.post(
    "/site-crawl",
    response_model=SiteCrawlResponse,
    status_code=status.HTTP_200_OK,
    summary="Crawl a domain's same-host pages and extract IOCs",
    description=(
        "Crawl a domain starting from its HTTPS homepage, following only same-host links up to "
        "a bounded page count/depth, and extract IOCs (secrets, JS endpoints, emails, URLs, "
        "and more) from every fetched page"
    ),
)
@limiter.limit("10/minute")  # heavier than other domain_finder checks: many outbound requests/call
async def site_crawl_post(request: Request, crawl_request: SiteCrawlRequest) -> SiteCrawlResponse:
    """Perform a bounded same-host site crawl via POST request"""
    logger.info(
        "POST site crawl request - Domain: %s, max_pages: %s, max_depth: %s",
        crawl_request.domain,
        crawl_request.max_pages,
        crawl_request.max_depth,
    )
    result = await perform_site_crawl(crawl_request)
    logger.info(
        "POST site crawl completed - Domain: %s, Pages: %s, IOCs: %s",
        crawl_request.domain,
        result.total_pages_crawled,
        result.iocs.statistics.total_unique_iocs,
    )
    return result


@router.get(
    "/site-crawl/{domain}",
    response_model=SiteCrawlResponse,
    status_code=status.HTTP_200_OK,
    summary="Crawl a domain's same-host pages and extract IOCs via URL parameter",
    description="Crawl a domain's same-host pages using domain from URL path for simple GET "
    "requests, with optional max_pages/max_depth query parameters",
)
@limiter.limit("10/minute")
async def site_crawl_get(
    request: Request, domain: str, max_pages: int = 15, max_depth: int = 2
) -> SiteCrawlResponse:
    """Perform a bounded same-host site crawl using domain from URL path via GET request"""
    logger.info(
        "GET site crawl request - Domain: %s, max_pages: %s, max_depth: %s",
        domain,
        max_pages,
        max_depth,
    )
    crawl_request = SiteCrawlRequest(domain=domain, max_pages=max_pages, max_depth=max_depth)
    result = await perform_site_crawl(crawl_request)
    logger.info(
        "GET site crawl completed - Domain: %s, Pages: %s, IOCs: %s",
        domain,
        result.total_pages_crawled,
        result.iocs.statistics.total_unique_iocs,
    )
    return result


@router.get(
    "/health",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Check domain lookup service health",
    description="Health check endpoint for the domain lookup service",
)
async def check_domain_service_health() -> dict[str, Any]:
    """Check if the domain lookup service is operational"""
    return {
        "service": "domain_lookup",
        "status": "healthy",
        "endpoints": [
            "/api/domain/lookup",
            "/api/domain/lookup/{domain}",
            "/api/domain/whois",
            "/api/domain/whois/{domain}",
            "/api/domain/ct-subdomains",
            "/api/domain/ct-subdomains/{domain}",
            "/api/domain/hackertarget-subdomains",
            "/api/domain/hackertarget-subdomains/{domain}",
            "/api/domain/rapiddns-subdomains",
            "/api/domain/rapiddns-subdomains/{domain}",
            "/api/domain/subfinder-subdomains",
            "/api/domain/subfinder-subdomains/{domain}",
            "/api/domain/host-probe",
            "/api/domain/host-probe/{domain}",
            "/api/domain/ssl-info",
            "/api/domain/ssl-info/{domain}",
            "/api/domain/security-headers",
            "/api/domain/security-headers/{domain}",
            "/api/domain/dnssec",
            "/api/domain/dnssec/{domain}",
            "/api/domain/blocklist",
            "/api/domain/blocklist/{domain}",
            "/api/domain/dns",
            "/api/domain/dns/{domain}",
            "/api/domain/dnsdumpster",
            "/api/domain/dnsdumpster/{domain}",
            "/api/domain/wayback",
            "/api/domain/wayback/{domain}",
            "/api/domain/temporal-analysis",
            "/api/domain/temporal-analysis/{domain}",
            "/api/domain/site-crawl",
            "/api/domain/site-crawl/{domain}",
        ],
        "subfinder_installed": is_subfinder_available(),
        "subfinder_version": get_subfinder_version(),
        "httpx_installed": is_httpx_available(),
        "httpx_version": get_httpx_version(),
    }
