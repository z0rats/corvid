"""Best-effort scrape of a domain's homepage for schema.org JSON-LD temporal
fields (dateCreated/dateModified/datePublished), feeding temporal_analysis_service.

Unlike youtube_page_service.py's fixed-host scrape, the domain here is
user-supplied and used to build the fetch URL, so this goes through
ssrf_guard's safe_get - the same pattern security_headers_service.py uses for
its own fetch of the user-supplied domain.
"""

import json
import logging
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.config.settings import settings
from app.core.security.ssrf_guard import SSRFValidationError, safe_get
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import SchemaOrgDate

logger = logging.getLogger(__name__)

SCHEMA_ORG_TIMEOUT = 10.0
DEFAULT_HEADERS = {"User-Agent": "Corvid-Domain-Lookup/1.0"}
_DATE_FIELDS = ("dateCreated", "dateModified", "datePublished")


async def fetch_schema_org_dates(domain: str) -> list[SchemaOrgDate]:
    """Fetch the domain's homepage and extract schema.org JSON-LD date fields.

    Best-effort, like youtube_page_service.py's scrape: any failure (SSRF
    rejection, connection error, non-2xx, malformed JSON-LD) returns an empty
    list rather than raising, since this is one of several temporal-analysis
    sources and shouldn't block the others.
    """
    url = f"https://{domain}"
    try:
        async with httpx.AsyncClient(
            timeout=SCHEMA_ORG_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=False
        ) as client:
            response = await safe_get(
                client, url, allow_private=settings.security.allow_private_network_targets
            )
            response.raise_for_status()
    except (SSRFValidationError, httpx.HTTPError) as e:
        logger.info("Could not fetch %s for schema.org scrape: %s", url, e)
        return []
    except Exception:
        logger.warning("Unexpected error scraping schema.org dates for %s", domain, exc_info=True)
        return []

    return _extract_dates(response.text)


def _extract_dates(html: str) -> list[SchemaOrgDate]:
    soup = BeautifulSoup(html, "lxml")
    dates: list[SchemaOrgDate] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError, TypeError:
            continue

        for obj in _flatten_json_ld(payload):
            for field in _DATE_FIELDS:
                value = obj.get(field)
                parsed = _parse_date(value) if isinstance(value, str) else None
                if parsed:
                    dates.append(SchemaOrgDate(field=field, value=parsed))

    return dates


def _flatten_json_ld(payload: Any) -> list[dict[str, Any]]:
    """A JSON-LD block can be a single object, a list of objects, or a
    top-level `@graph` wrapping either - normalize to a flat list of dicts."""
    if isinstance(payload, dict):
        graph = payload.get("@graph")
        if isinstance(graph, list):
            return [item for item in graph if isinstance(item, dict)]
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _parse_date(date_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None
