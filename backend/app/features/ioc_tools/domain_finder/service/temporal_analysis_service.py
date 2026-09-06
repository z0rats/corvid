"""Aggregates WHOIS/SSL/Wayback/schema.org dates for a domain into one
chronological timeline. Reuses each panel's existing service function rather
than re-implementing their fetches; a single source failing (e.g. no TLS
listener, RDAP lookup miss) doesn't fail the whole request - it's recorded in
`sources_failed` and simply contributes no events.
"""

import asyncio
import logging
from collections.abc import Coroutine
from datetime import datetime
from typing import Any

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    SchemaOrgDate,
    SslInfoRequest,
    SslInfoResponse,
    TemporalAnalysisRequest,
    TemporalAnalysisResponse,
    TemporalEvent,
    TemporalEventSource,
    WaybackLookupRequest,
    WaybackLookupResponse,
    WhoisLookupRequest,
    WhoisLookupResponse,
)
from app.features.ioc_tools.domain_finder.service.schema_org_service import fetch_schema_org_dates
from app.features.ioc_tools.domain_finder.service.ssl_info_service import perform_ssl_info_lookup
from app.features.ioc_tools.domain_finder.service.wayback_lookup_service import (
    perform_wayback_lookup,
)
from app.features.ioc_tools.domain_finder.service.whois_lookup_service import perform_whois_lookup

logger = logging.getLogger(__name__)

_SCHEMA_ORG_LABELS = {
    "dateCreated": "Page Created (schema.org)",
    "dateModified": "Page Modified (schema.org)",
    "datePublished": "Page Published (schema.org)",
}

# (date, category, label) - the raw shape each source's extractor produces,
# before it's stamped with its source name into a TemporalEvent.
_RawEvent = tuple[datetime, str, str]


def _whois_events(whois: WhoisLookupResponse) -> list[_RawEvent]:
    candidates = [
        (whois.creation_date, "Domain Registered"),
        (whois.updated_date, "Domain Updated"),
        (whois.expiration_date, "Domain Expires"),
    ]
    return [(date, "server", label) for date, label in candidates if date]


def _ssl_events(ssl: SslInfoResponse) -> list[_RawEvent]:
    return [
        (ssl.not_before, "server", "SSL Valid From"),
        (ssl.not_after, "server", "SSL Valid Until"),
    ]


def _wayback_events(wayback: WaybackLookupResponse) -> list[_RawEvent]:
    candidates = [
        (wayback.first_capture, "First Archived"),
        (wayback.last_capture, "Last Archived"),
    ]
    return [(date, "page", label) for date, label in candidates if date]


def _schema_org_events(dates: list[SchemaOrgDate]) -> list[_RawEvent]:
    return [(entry.value, "page", _SCHEMA_ORG_LABELS[entry.field]) for entry in dates]


def _events_for(source: TemporalEventSource, result: Any) -> list[_RawEvent]:
    """Dispatch a successful source result to its own extractor - one place
    that knows every source, instead of a repeated if/else per source at the
    call site."""
    match source:
        case "whois":
            return _whois_events(result)
        case "ssl_certificate":
            return _ssl_events(result)
        case "wayback":
            return _wayback_events(result)
        case "schema_org":
            return _schema_org_events(result)


async def _safe_call[T](source: str, coro: Coroutine[Any, Any, T]) -> T | Exception:
    """Run one source's lookup, swallowing its failure into the return value
    (rather than propagating) so `asyncio.gather` always completes."""
    try:
        return await coro
    except AppHTTPException as e:
        logger.info("Temporal analysis source '%s' failed for this domain: %s", source, e.detail)
        return e
    except Exception as e:
        logger.warning(
            "Temporal analysis source '%s' raised unexpectedly: %s", source, e, exc_info=True
        )
        return e


async def perform_temporal_analysis(request: TemporalAnalysisRequest) -> TemporalAnalysisResponse:
    """
    Build a chronological timeline of domain/page dates from WHOIS, the live TLS
    certificate, Wayback Machine capture history, and the homepage's schema.org
    JSON-LD.

    Args:
        request: Validated temporal analysis request

    Returns:
        TemporalAnalysisResponse with all extracted events sorted oldest first,
        plus any sources that could not be fetched for this domain
    """
    domain = request.domain
    logger.info("Starting temporal analysis for: %s", domain)

    sources: list[TemporalEventSource] = ["whois", "ssl_certificate", "wayback", "schema_org"]
    results = await asyncio.gather(
        _safe_call("whois", perform_whois_lookup(WhoisLookupRequest(domain=domain))),
        _safe_call("ssl_certificate", perform_ssl_info_lookup(SslInfoRequest(domain=domain))),
        _safe_call("wayback", perform_wayback_lookup(WaybackLookupRequest(domain=domain))),
        _safe_call("schema_org", fetch_schema_org_dates(domain)),
    )

    events: list[TemporalEvent] = []
    sources_failed: list[TemporalEventSource] = []
    for source, result in zip(sources, results, strict=True):
        if isinstance(result, Exception):
            sources_failed.append(source)
            continue
        for date, category, label in _events_for(source, result):
            events.append(TemporalEvent(date=date, category=category, source=source, label=label))

    events.sort(key=lambda e: e.date)

    response = TemporalAnalysisResponse(domain=domain, events=events, sources_failed=sources_failed)
    logger.info(
        "Temporal analysis completed for %s - %s events, sources failed: %s",
        domain,
        len(events),
        sources_failed,
    )
    return response
