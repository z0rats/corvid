"""
Passive subdomain enumeration via RapidDNS's public subdomain lookup page.

rapiddns.io has no JSON API for this - `/subdomain/<domain>?full=1` serves an
HTML page with a `#table` of DNS records aggregated from public passive-DNS
sources (one row per hostname/record-type/resolved-value). Parsed with the
stdlib `html.parser` rather than adding a `beautifulsoup4` dependency for one
source - the table markup is simple, fixed, and doesn't need a real DOM.
"""

import logging
from html.parser import HTMLParser

import httpx

from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

RAPIDDNS_URL = "https://rapiddns.io/subdomain/{domain}"
RAPIDDNS_TIMEOUT = 20.0
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0",
    "Accept": "text/html",
}


class _SubdomainTableParser(HTMLParser):
    """Extracts rows from the `<tbody>` of RapidDNS's results table.

    Each row is `[#, hostname, address, record_type, date]` - the `address`
    cell wraps its value in a `<a>` (a same-IP pivot link), so cell text is
    accumulated across nested tags rather than read from a single text node.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_tbody = False
        self._in_cell = False
        self._cell_parts: list[str] = []
        self._row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._row = []
        elif tag in ("td", "th") and self._in_tbody:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self._in_tbody = False
        elif tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            self._row.append("".join(self._cell_parts).strip())
        elif tag == "tr" and self._in_tbody and self._row:
            self.rows.append(self._row)
            self._row = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)


async def fetch_rapiddns_records(domain: str) -> list[tuple[str, str, str]]:
    """
    Fetch raw (hostname, record_type, address) rows for a domain from RapidDNS.

    Args:
        domain: Domain name to search for

    Returns:
        List of (hostname, record_type, address) tuples

    Raises:
        AppHTTPException: For request failures
    """
    logger.debug("Fetching RapidDNS subdomain data for domain: %s", domain)

    try:
        async with httpx.AsyncClient(timeout=RAPIDDNS_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            response = await client.get(RAPIDDNS_URL.format(domain=domain), params={"full": "1"})
            response.raise_for_status()

            if not response.text.strip():
                logger.info("RapidDNS returned an empty response for domain: %s", domain)
                return []

            parser = _SubdomainTableParser()
            parser.feed(response.text)

            records: list[tuple[str, str, str]] = []
            for row in parser.rows:
                if len(row) < 4:
                    # Markup drifted from the shape this parser expects - skip
                    # rather than misinterpret a partial row
                    continue
                _index, hostname, address, record_type = row[:4]
                if hostname and record_type:
                    records.append((hostname, record_type, address))

            logger.info("Retrieved %s records from RapidDNS for domain: %s", len(records), domain)
            return records

    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching RapidDNS data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to RapidDNS",
            error_code="RAPIDDNS_TIMEOUT",
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error while fetching RapidDNS data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to RapidDNS: {str(e)}",
            error_code="RAPIDDNS_CONNECTION_ERROR",
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP status error from RapidDNS for domain %s: Status %s",
            domain,
            e.response.status_code,
        )
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"RapidDNS returned error: {e.response.status_code}",
            error_code="RAPIDDNS_API_ERROR",
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error while fetching RapidDNS data for domain %s: %s",
            domain,
            e,
            exc_info=True,
        )
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching RapidDNS data",
            error_code="RAPIDDNS_UNEXPECTED_ERROR",
        ) from e
