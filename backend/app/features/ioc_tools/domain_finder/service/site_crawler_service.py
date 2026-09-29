"""
Bounded same-host crawler, closing out the last open piece of the Photon
integration (regex patterns were ported earlier straight into
ioc_extractor_service.py's IOC_PATTERNS, this is the crawler half). Written fresh
against our own SSRF-guarded client rather than translated from Photon's
`requests`-based crawler, so no attribution is needed (Photon is GPL-3.0, compatible
with our AGPLv3 as a GPLv3->AGPLv3 upgrade anyway).

Walks same-host `<a href>`/`<script src>` links breadth-first via
`ssrf_guard.safe_get`, and runs every fetched page's raw text through the
same regex engine as the standalone IOC Extractor tool (`ioc_extractor_service`)
- the crawler's whole value is feeding that extractor pages an analyst would
otherwise have to open one by one (secrets, JS API endpoints, emails, embedded
URLs, ...), aggregated into one response.

Bounded and synchronous like the rest of domain_finder (capped pages/depth,
single request/response) rather than a job/polling model - crawls here are
small enough (<= SiteCrawlRequest.max_pages, hard-capped at 30) and fast
enough that streaming progress isn't worth departing from every other panel
in this sub-feature.
"""

import logging
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from app.core.config.settings import settings
from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError, safe_get
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    CrawledPage,
    SiteCrawlRequest,
    SiteCrawlResponse,
)
from app.features.ioc_tools.ioc_extractor.schemas.extractor_schemas import ExtractionResponse
from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import (
    calculate_extraction_statistics,
    deduplicate_extracted_iocs,
    filter_domains_from_ips,
    process_content_for_iocs,
)
from app.features.ioc_tools.ioc_extractor.utils.validation_utils import sanitize_text_content

logger = logging.getLogger(__name__)

CRAWL_TIMEOUT = 15.0
DEFAULT_HEADERS: dict[str, str] = {"User-Agent": "Corvid-Domain-Lookup/1.0"}
# Caps how much of one page's body feeds the regex pass - keeps memory/CPU
# bounded against a pathological multi-hundred-MB response.
MAX_CONTENT_CHARS = 2_000_000

IOC_TYPES = (
    "ips",
    "md5",
    "sha1",
    "sha256",
    "urls",
    "domains",
    "emails",
    "cves",
    "secrets",
    "js_endpoints",
)


class _LinkExtractor(HTMLParser):
    """Collects `<a href>`/`<script src>` targets and the `<title>` text from one page."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.title: str | None = None
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        href = attr_dict.get("href")
        src = attr_dict.get("src")
        if tag == "a" and href:
            self.links.append(href)
        elif tag == "script" and src:
            self.links.append(src)
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title = (self.title or "") + data


def _normalize_url(url: str) -> str:
    """Strip the fragment so `#anchor` variants of the same page dedupe together."""
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


def _is_same_host_link(url: str, domain: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme in ("http", "https") and parsed.hostname == domain


async def perform_site_crawl(request: SiteCrawlRequest) -> SiteCrawlResponse:
    """
    Crawl a domain's same-host pages/scripts and aggregate IOCs found across them.

    Args:
        request: Validated site crawl request

    Returns:
        SiteCrawlResponse with per-page metadata and aggregated IOCs

    Raises:
        AppHTTPException: If the entry page (the domain's homepage) itself can't be
            fetched - a page unreachable deeper in the crawl is recorded in
            `errors` instead, since partial results are still useful there.
    """
    domain = request.domain
    start_url = f"https://{domain}/"
    logger.info(
        "Starting site crawl for %s (max_pages=%s, max_depth=%s)",
        domain,
        request.max_pages,
        request.max_depth,
    )

    queue: deque[tuple[str, int]] = deque([(start_url, 0)])
    visited: set[str] = set()
    pages: list[CrawledPage] = []
    errors: list[str] = []
    raw_iocs: dict[str, list[str]] = {ioc_type: [] for ioc_type in IOC_TYPES}

    async with httpx.AsyncClient(
        timeout=CRAWL_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=False
    ) as client:
        while queue and len(pages) < request.max_pages:
            url, depth = queue.popleft()
            normalized = _normalize_url(url)
            if normalized in visited:
                continue
            visited.add(normalized)
            is_entry_page = url == start_url

            try:
                response = await safe_get(
                    client, url, allow_private=settings.security.allow_private_network_targets
                )
            except SSRFValidationError as e:
                if is_entry_page:
                    logger.warning("SSRF validation failed for site crawl on %s: %s", domain, e)
                    raise AppHTTPException(
                        status_code=400, detail=str(e), error_code="SITE_CRAWL_INVALID_HOST"
                    ) from e
                errors.append(f"{url}: {e}")
                continue
            except httpx.TimeoutException as e:
                if is_entry_page:
                    logger.error("Timeout while crawling entry page for %s: %s", domain, e)
                    raise AppHTTPException(
                        status_code=504,
                        detail="Request timeout while connecting",
                        error_code="SITE_CRAWL_TIMEOUT",
                    ) from e
                errors.append(f"{url}: timed out")
                continue
            except httpx.RequestError as e:
                if is_entry_page:
                    logger.error("Request error while crawling entry page for %s: %s", domain, e)
                    raise AppHTTPException(
                        status_code=503,
                        detail=f"Failed to connect to {domain}: {str(e)}",
                        error_code="SITE_CRAWL_CONNECTION_ERROR",
                    ) from e
                errors.append(f"{url}: {e}")
                continue
            except Exception as e:  # noqa: BLE001 - one bad page shouldn't abort the whole crawl
                if is_entry_page:
                    logger.error(
                        "Unexpected error crawling entry page for %s: %s", domain, e, exc_info=True
                    )
                    raise AppHTTPException(
                        status_code=500,
                        detail="An unexpected error occurred while crawling the site",
                        error_code="SITE_CRAWL_UNEXPECTED_ERROR",
                    ) from e
                errors.append(f"{url}: {e}")
                continue

            content_type = response.headers.get("content-type", "")
            text = response.text[:MAX_CONTENT_CHARS]
            is_html = "html" in content_type.lower() or (
                not content_type and text.lstrip().startswith("<")
            )

            title: str | None = None
            if is_html and text:
                extractor = _LinkExtractor()
                try:
                    extractor.feed(text)
                except Exception:  # noqa: BLE001 - malformed markup shouldn't abort the crawl
                    extractor = _LinkExtractor()
                title = extractor.title.strip() if extractor.title else None

                if depth < request.max_depth:
                    for link in extractor.links:
                        absolute = urljoin(url, link)
                        if (
                            _is_same_host_link(absolute, domain)
                            and _normalize_url(absolute) not in visited
                        ):
                            queue.append((absolute, depth + 1))

            pages.append(
                CrawledPage(
                    url=url,
                    status_code=response.status_code,
                    content_type=content_type or None,
                    title=title,
                    depth=depth,
                )
            )

            sanitized = sanitize_text_content(text)
            if sanitized:
                page_iocs = process_content_for_iocs(sanitized)
                for ioc_type, values in page_iocs.items():
                    raw_iocs[ioc_type].extend(values)

    unique_iocs = deduplicate_extracted_iocs(raw_iocs)
    filtered_domains = filter_domains_from_ips(unique_iocs["domains"])
    statistics = calculate_extraction_statistics(raw_iocs, unique_iocs, filtered_domains)

    iocs = ExtractionResponse(
        ips=unique_iocs["ips"],
        md5=unique_iocs["md5"],
        sha1=unique_iocs["sha1"],
        sha256=unique_iocs["sha256"],
        urls=unique_iocs["urls"],
        domains=filtered_domains,
        emails=unique_iocs["emails"],
        cves=unique_iocs["cves"],
        secrets=unique_iocs["secrets"],
        js_endpoints=unique_iocs["js_endpoints"],
        statistics=statistics,
    )

    result = SiteCrawlResponse(
        domain=domain, pages=pages, total_pages_crawled=len(pages), iocs=iocs, errors=errors
    )
    logger.info(
        "Site crawl completed for %s - %s pages, %s unique IOCs, %s errors",
        domain,
        len(pages),
        statistics.total_unique_iocs,
        len(errors),
    )
    return result
