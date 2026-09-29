"""safe_get is monkeypatched directly (rather than exercised through real DNS
resolution/SSRF checks, already covered by test_ssrf_guard.py) so these tests
focus on perform_site_crawl's own logic: same-host link following, depth/page
bounds, per-page IOC aggregation, and error handling (entry page failures
raise, deeper-page failures are recorded and the crawl continues)."""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import SiteCrawlRequest
from app.features.ioc_tools.domain_finder.service import site_crawler_service
from app.features.ioc_tools.domain_finder.service.site_crawler_service import perform_site_crawl

ENTRY_HTML = """
<html><head><title>Home</title></head><body>
<a href="/about">About</a>
<a href="https://example.com/contact">Contact</a>
<a href="https://external.com/other">External</a>
<script src="/static/app.js"></script>
secret: AKIAABCDEFGHIJKLMNOP contact us at admin@example.com
</body></html>
"""

ABOUT_HTML = """
<html><head><title>About</title></head><body>
call 8.8.8.8 or visit http://example.com/deep
<a href="/deep">Deep page</a>
</body></html>
"""

CONTACT_HTML = """
<html><head><title>Contact</title></head><body>
email: sales@example.com
</body></html>
"""

APP_JS = 'fetch("/api/v1/users").then(r => r.json());'

PAGES = {
    "https://example.com/": (200, "text/html; charset=utf-8", ENTRY_HTML),
    "https://example.com/about": (200, "text/html; charset=utf-8", ABOUT_HTML),
    "https://example.com/contact": (200, "text/html; charset=utf-8", CONTACT_HTML),
    "https://example.com/static/app.js": (200, "application/javascript", APP_JS),
}


def _run(coro):
    return asyncio.run(coro)


def _patch_safe_get(monkeypatch, pages=PAGES, exc_for=None):
    async def fake_safe_get(client, url, **kwargs):
        if exc_for and url == exc_for[0]:
            raise exc_for[1]
        if url not in pages:
            raise AssertionError(f"Unexpected fetch of {url} - not on the same-host allowlist")
        status_code, content_type, text = pages[url]
        return httpx.Response(status_code, headers={"content-type": content_type}, text=text)

    monkeypatch.setattr(site_crawler_service, "safe_get", fake_safe_get)


def test_crawls_same_host_pages_and_aggregates_iocs(monkeypatch):
    _patch_safe_get(monkeypatch)

    result = _run(
        perform_site_crawl(SiteCrawlRequest(domain="example.com", max_pages=10, max_depth=1))
    )

    crawled_urls = {page.url for page in result.pages}
    assert crawled_urls == {
        "https://example.com/",
        "https://example.com/about",
        "https://example.com/contact",
        "https://example.com/static/app.js",
    }
    assert result.total_pages_crawled == 4
    assert not result.errors

    entry_page = next(p for p in result.pages if p.url == "https://example.com/")
    assert entry_page.title == "Home"
    assert entry_page.depth == 0

    assert "AKIAABCDEFGHIJKLMNOP" in result.iocs.secrets
    assert "admin@example.com" in result.iocs.emails
    assert "sales@example.com" in result.iocs.emails
    assert "8.8.8.8" in result.iocs.ips
    assert "http://example.com/deep" in result.iocs.urls
    assert "/api/v1/users" in result.iocs.js_endpoints
    assert "example.com" in result.iocs.domains


def test_stops_following_links_beyond_max_depth(monkeypatch):
    _patch_safe_get(monkeypatch)

    result = _run(
        perform_site_crawl(SiteCrawlRequest(domain="example.com", max_pages=10, max_depth=1))
    )

    # /deep is only linked from /about, which is already at depth 1 - with
    # max_depth=1 its own links must not be followed.
    assert "https://example.com/deep" not in {page.url for page in result.pages}


def test_respects_max_pages_cap(monkeypatch):
    _patch_safe_get(monkeypatch)

    result = _run(
        perform_site_crawl(SiteCrawlRequest(domain="example.com", max_pages=1, max_depth=2))
    )

    assert result.total_pages_crawled == 1
    assert result.pages[0].url == "https://example.com/"


def test_never_fetches_external_host_links(monkeypatch):
    _patch_safe_get(monkeypatch)

    result = _run(
        perform_site_crawl(SiteCrawlRequest(domain="example.com", max_pages=10, max_depth=2))
    )

    assert all(page.url.startswith("https://example.com/") for page in result.pages)


def test_deeper_page_failure_is_recorded_not_raised(monkeypatch):
    _patch_safe_get(
        monkeypatch, exc_for=("https://example.com/about", httpx.ConnectError("refused"))
    )

    result = _run(
        perform_site_crawl(SiteCrawlRequest(domain="example.com", max_pages=10, max_depth=1))
    )

    assert any("about" in err for err in result.errors)
    assert "https://example.com/about" not in {page.url for page in result.pages}
    # The rest of the crawl still completes
    assert "https://example.com/contact" in {page.url for page in result.pages}


def test_raises_400_on_ssrf_validation_failure_for_entry_page(monkeypatch):
    _patch_safe_get(
        monkeypatch,
        exc_for=("https://example.com/", SSRFValidationError("resolves to a private address")),
    )

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_site_crawl(SiteCrawlRequest(domain="example.com")))

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "SITE_CRAWL_INVALID_HOST"


def test_raises_504_on_timeout_for_entry_page(monkeypatch):
    _patch_safe_get(
        monkeypatch, exc_for=("https://example.com/", httpx.TimeoutException("timed out"))
    )

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_site_crawl(SiteCrawlRequest(domain="example.com")))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "SITE_CRAWL_TIMEOUT"


def test_raises_503_on_connection_error_for_entry_page(monkeypatch):
    _patch_safe_get(monkeypatch, exc_for=("https://example.com/", httpx.ConnectError("refused")))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_site_crawl(SiteCrawlRequest(domain="example.com")))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "SITE_CRAWL_CONNECTION_ERROR"


def test_site_crawl_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        SiteCrawlRequest(domain="example-*")


def test_site_crawl_request_enforces_page_and_depth_bounds():
    with pytest.raises(ValueError):
        SiteCrawlRequest(domain="example.com", max_pages=31)
    with pytest.raises(ValueError):
        SiteCrawlRequest(domain="example.com", max_depth=4)
