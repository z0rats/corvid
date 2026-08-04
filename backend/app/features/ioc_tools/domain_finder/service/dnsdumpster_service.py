"""
DNSDumpster domain lookup business logic: maps the raw DNSDumpster API response
into DnsDumpsterResponse, layered on top of domain_finder's existing WHOIS/DNS/CT
panels with ASN, geo, PTR, and HTTP(S) banner detail per resolved host.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    DnsDumpsterBanner,
    DnsDumpsterHost,
    DnsDumpsterIp,
    DnsDumpsterRequest,
    DnsDumpsterResponse,
)
from app.features.ioc_tools.domain_finder.service.dnsdumpster_api_service import fetch_dnsdumpster_data

logger = logging.getLogger(__name__)


async def perform_dnsdumpster_lookup(request: DnsDumpsterRequest, db: AsyncSession) -> DnsDumpsterResponse:
    """
    Perform a DNSDumpster domain lookup and map the response for the API.

    Args:
        request: Validated DNSDumpster request containing the domain to search
        db: Database session, used to fetch the configured DNSDumpster API key

    Returns:
        DnsDumpsterResponse containing DNS records enriched with ASN/geo/PTR/banner detail

    Raises:
        AppHTTPException: When no DNSDumpster API key is configured, or the API request fails
    """
    domain = request.domain
    api_key = await _get_dnsdumpster_key(db)

    logger.info("Starting DNSDumpster lookup for: %s", domain)
    raw_data = await fetch_dnsdumpster_data(domain, api_key)

    response = DnsDumpsterResponse(
        domain=domain,
        a=_parse_hosts(raw_data.get("a")),
        ns=_parse_hosts(raw_data.get("ns")),
        mx=_parse_hosts(raw_data.get("mx")),
        cname=_parse_hosts(raw_data.get("cname")),
        txt=[str(entry) for entry in (raw_data.get("txt") or [])],
        total_a_records=raw_data.get("total_a_recs") or 0,
    )

    logger.info("DNSDumpster lookup completed for %s - %s A records", domain, len(response.a))
    return response


async def _get_dnsdumpster_key(db: AsyncSession) -> str:
    """Fetch the DNSDumpster API key configured under Settings > API Keys."""
    apikey = await get_apikey(db=db, name="dnsdumpster")
    if not apikey or not apikey.is_active or not apikey.key:
        raise AppHTTPException(
            status_code=400,
            detail="DNSDumpster API key is not configured. Add one under Settings > API Keys.",
            error_code="DNSDUMPSTER_NOT_CONFIGURED",
        )
    return apikey.key


def _parse_hosts(raw_hosts: list[dict[str, Any]] | None) -> list[DnsDumpsterHost]:
    """Parse a raw DNSDumpster host-group (a/ns/mx/cname) into DnsDumpsterHost objects."""
    hosts: list[DnsDumpsterHost] = []
    for raw_host in raw_hosts or []:
        try:
            hosts.append(DnsDumpsterHost(
                host=raw_host.get("host"),
                ips=_parse_ips(raw_host.get("ips")),
            ))
        except Exception as e:
            logger.warning("Failed to parse DNSDumpster host entry: %s", e)
            continue
    return hosts


def _parse_ips(raw_ips: list[dict[str, Any]] | None) -> list[DnsDumpsterIp]:
    """Parse a raw DNSDumpster IP list into DnsDumpsterIp objects."""
    ips: list[DnsDumpsterIp] = []
    for raw_ip in raw_ips or []:
        try:
            banners = raw_ip.get("banners") or {}
            ips.append(DnsDumpsterIp(
                ip=raw_ip.get("ip"),
                asn=raw_ip.get("asn"),
                asn_name=raw_ip.get("asn_name"),
                asn_range=raw_ip.get("asn_range"),
                country=raw_ip.get("country"),
                country_code=raw_ip.get("country_code"),
                ptr=raw_ip.get("ptr"),
                banner_http=_parse_banner(banners.get("http")),
                banner_https=_parse_banner(banners.get("https")),
            ))
        except Exception as e:
            logger.warning("Failed to parse DNSDumpster IP entry: %s", e)
            continue
    return ips


def _parse_banner(raw_banner: dict[str, Any] | None) -> DnsDumpsterBanner | None:
    """Parse a raw DNSDumpster HTTP/HTTPS banner dict into a DnsDumpsterBanner."""
    if not raw_banner:
        return None
    return DnsDumpsterBanner(
        server=raw_banner.get("server"),
        title=raw_banner.get("title"),
        cn=raw_banner.get("cn"),
        apps=list(raw_banner.get("apps") or []),
    )
