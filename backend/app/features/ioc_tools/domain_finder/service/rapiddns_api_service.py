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

from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

RAPIDDNS = Provider(
    name="RapidDNS", code="RAPIDDNS", base_url="https://rapiddns.io/subdomain/", accept="text/html"
)


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
    """Raw (hostname, record_type, address) rows for a domain from RapidDNS. Failures raise
    `AppHTTPException` (`provider_http`)."""

    def parse(response: httpx.Response) -> list[tuple[str, str, str]]:
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

    return await provider_get(RAPIDDNS, domain, subject=domain, params={"full": "1"}, parse=parse)
