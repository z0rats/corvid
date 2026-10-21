"""`WebContentFetcher` pulls user-supplied URLs into LLM prompts, so beyond
the HTML-to-text extraction the important property is that every fetch,
including each redirect hop, goes through `ssrf_guard` and fails closed."""

import socket

import httpx
import pytest

from app.features.llm_templates.utils import web_content_fetcher as wcf
from app.features.llm_templates.utils.web_content_fetcher import (
    WebContentFetcher,
    fetch_web_contexts,
    format_web_contexts_for_prompt,
)
from tests.conftest import run

PUBLIC_IP = "93.184.216.34"


def _addrinfo(ip):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]


@pytest.fixture
def dns(monkeypatch):
    """Map hostnames to IPs for the SSRF guard's resolution step."""
    table: dict[str, str] = {}

    def fake_getaddrinfo(host, *a, **k):
        if host in table:
            return _addrinfo(table[host])
        if host.replace(".", "").isdigit():
            return _addrinfo(host)
        raise socket.gaierror("unknown host")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(wcf.settings.security, "allow_private_network_targets", False)
    return table


def _html(body: str, title: str = "Page") -> str:
    return f"<html><head><title>{title}</title></head><body>{body}</body></html>"


def _fetch(url):
    async def go():
        async with WebContentFetcher() as f:
            return await f.fetch_content(url)

    return run(go())


class TestSsrfProtection:
    def test_url_resolving_to_private_ip_is_refused_without_a_request(
        self, dns, patch_httpx_transport
    ):
        dns["internal.example"] = "10.0.0.5"
        calls = []
        patch_httpx_transport(lambda req: calls.append(req) or httpx.Response(200))

        ok, msg, title = _fetch("http://internal.example/admin")

        assert ok is False
        assert msg.startswith("URL validation failed")
        assert title is None
        assert calls == []

    @pytest.mark.parametrize("ip", ["127.0.0.1", "169.254.169.254"])
    def test_literal_loopback_and_metadata_ips_are_refused(self, dns, patch_httpx_transport, ip):
        patch_httpx_transport(lambda req: httpx.Response(200))
        ok, msg, _ = _fetch(f"http://{ip}/latest/meta-data")
        assert ok is False
        assert "validation failed" in msg

    def test_redirect_to_private_host_is_refused(self, dns, patch_httpx_transport):
        dns["public.example"] = PUBLIC_IP
        dns["evil-internal.example"] = "192.168.1.1"

        def handler(req):
            return httpx.Response(302, headers={"location": "http://evil-internal.example/"})

        patch_httpx_transport(handler)
        ok, msg, _ = _fetch("http://public.example/")
        assert ok is False
        assert "validation failed" in msg

    @pytest.mark.parametrize(
        "url", ["file:///etc/passwd", "ftp://example.com/x", "gopher://x", "http://", "nonsense"]
    )
    def test_non_http_or_hostless_urls_rejected_up_front(self, url):
        ok, msg, _ = _fetch(url)
        assert ok is False
        assert msg.startswith("URL validation failed")


class TestFetchContent:
    def test_successful_fetch_returns_title_and_main_content(self, dns, patch_httpx_transport):
        dns["site.example"] = PUBLIC_IP
        body = (
            "<nav>NAVIGATION</nav><script>alert('x')</script>"
            "<article><h1>Headline</h1><p>Real content here.</p></article>"
            "<footer>FOOTER</footer>"
        )
        patch_httpx_transport(
            lambda req: httpx.Response(
                200, text=_html(body, " My Title "), headers={"content-type": "text/html"}
            )
        )

        ok, content, title = _fetch("https://site.example/post")

        assert ok is True
        assert title == "My Title"
        assert "Headline" in content
        assert "Real content here." in content
        for junk in ("NAVIGATION", "alert", "FOOTER"):
            assert junk not in content

    def test_non_html_content_type_rejected(self, dns, patch_httpx_transport):
        dns["site.example"] = PUBLIC_IP
        patch_httpx_transport(
            lambda req: httpx.Response(
                200, content=b"%PDF", headers={"content-type": "application/pdf"}
            )
        )
        ok, msg, _ = _fetch("https://site.example/doc.pdf")
        assert ok is False
        assert "Unsupported content type: application/pdf" == msg

    def test_oversized_body_rejected(self, dns, patch_httpx_transport, monkeypatch):
        dns["site.example"] = PUBLIC_IP
        monkeypatch.setattr(WebContentFetcher, "MAX_CONTENT_SIZE", 100)
        patch_httpx_transport(
            lambda req: httpx.Response(
                200, text=_html("x" * 500), headers={"content-type": "text/html"}
            )
        )
        ok, msg, _ = _fetch("https://site.example/")
        assert ok is False
        assert msg.startswith("Content too large")

    def test_http_error_status_reported(self, dns, patch_httpx_transport):
        dns["site.example"] = PUBLIC_IP
        patch_httpx_transport(lambda req: httpx.Response(404))
        ok, msg, _ = _fetch("https://site.example/missing")
        assert ok is False
        assert msg == "HTTP 404 error for https://site.example/missing"

    def test_timeout_reported(self, dns, patch_httpx_transport):
        dns["site.example"] = PUBLIC_IP

        def handler(req):
            raise httpx.ReadTimeout("slow", request=req)

        patch_httpx_transport(handler)
        ok, msg, _ = _fetch("https://site.example/")
        assert ok is False
        assert msg.startswith("Timeout while fetching")


class TestExtraction:
    def test_falls_back_to_body_and_drops_separator_lines(self):
        f = WebContentFetcher()
        try:
            text = f._extract_text_content(
                "<html><body><p>Alpha</p><hr><p>Beta</p></body></html>", "u"
            )
        finally:
            run(f.client.aclose())
        assert text.splitlines() == ["Alpha", "Beta"]

    def test_truncates_overlong_extracted_text(self, monkeypatch):
        monkeypatch.setattr(WebContentFetcher, "MAX_CONTENT_SIZE", 20)
        f = WebContentFetcher()
        try:
            text = f._extract_text_content(f"<main><p>{'word ' * 50}</p></main>", "u")
        finally:
            run(f.client.aclose())
        assert text.endswith("[Content truncated due to size limit]")
        assert len(text) < 80


class TestMultipleUrls:
    def test_blank_urls_skipped_and_failures_kept_as_error_entries(
        self, dns, patch_httpx_transport
    ):
        dns["ok.example"] = PUBLIC_IP
        patch_httpx_transport(
            lambda req: httpx.Response(
                200, text=_html("<main>hello</main>", "T"), headers={"content-type": "text/html"}
            )
        )

        results = run(
            fetch_web_contexts(
                [
                    {"url": "  ", "name": "blank"},
                    {"url": "https://ok.example/", "name": "Good", "description": "d"},
                    {"url": "file:///etc/passwd", "name": "Bad"},
                ]
            )
        )

        by_name = {r["name"]: r for r in results}
        assert set(by_name) == {"Good", "Bad"}
        assert by_name["Good"]["success"] is True
        assert by_name["Good"]["error"] is None
        assert by_name["Bad"]["success"] is False
        assert by_name["Bad"]["error"].startswith("URL validation failed")

    def test_empty_inputs(self):
        assert run(fetch_web_contexts([])) == []
        assert run(fetch_web_contexts([{"url": ""}])) == []


class TestFormatForPrompt:
    def test_formats_success_and_failure_sections(self):
        out = format_web_contexts_for_prompt(
            [
                {
                    "success": True,
                    "name": "Report",
                    "title": "Vendor Blog",
                    "url": "https://a",
                    "description": "context",
                    "content": "BODY",
                },
                {"success": False, "name": "Down", "url": "https://b", "error": "HTTP 500"},
            ]
        )
        first, second = out.split("\n\n---\n\n")
        assert first.startswith("## Report (Vendor Blog)")
        assert "URL: https://a" in first
        assert "Description: context" in first
        assert first.endswith("BODY")
        assert second.startswith("## Down (FAILED)")
        assert "Error: HTTP 500" in second

    def test_title_equal_to_name_not_repeated_and_empty_description_omitted(self):
        out = format_web_contexts_for_prompt(
            [{"success": True, "name": "Same", "title": "Same", "url": "u", "content": "c"}]
        )
        assert out.splitlines()[0] == "## Same"
        assert "Description" not in out

    def test_empty(self):
        assert format_web_contexts_for_prompt([]) == ""
