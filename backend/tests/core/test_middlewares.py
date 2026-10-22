"""The three in-house ASGI middlewares `main.py` stacks on every request:
body-size limit, request-id propagation, and security headers.

Each is exercised on a bare Starlette app so the assertion is about the
middleware itself, not whatever a real route happens to return.
"""

import logging

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.config import body_limit_config, request_id_config, security_config
from app.core.config.body_limit_config import RequestBodyLimitMiddleware
from app.core.config.request_id_config import (
    MAX_REQUEST_ID_LENGTH,
    RequestIdLogFilter,
    RequestIdMiddleware,
    request_id_ctx,
)
from app.core.config.security_config import SecurityHeadersMiddleware

seen_request_ids: list[str | None] = []


async def _echo(request):
    body = await request.body()
    seen_request_ids.append(request_id_ctx.get())
    return PlainTextResponse(f"ok:{len(body)}")


def _csp_sources(csp: str) -> set[str]:
    """Every source token across all CSP directives (directive names dropped)."""
    return {token for directive in csp.split(";") for token in directive.split()[1:]}


def _app(middleware) -> TestClient:
    paths = ["/api/x", "/docs", "/redoc", "/openapi.json", "/static/a.js", "/feedicons/a.png"]
    app = Starlette(routes=[Route(p, _echo, methods=["GET", "POST"]) for p in paths])
    app.add_middleware(middleware)
    return TestClient(app)


class TestRequestBodyLimit:
    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setattr(body_limit_config.settings.api, "max_request_body_bytes", 10)
        return _app(RequestBodyLimitMiddleware)

    def test_body_within_limit_passes(self, client):
        r = client.post("/api/x", content=b"x" * 10)
        assert r.status_code == 200
        assert r.text == "ok:10"

    def test_body_over_limit_is_rejected_with_413(self, client):
        r = client.post("/api/x", content=b"x" * 11)
        assert r.status_code == 413
        assert r.json() == {"detail": "Request body too large"}

    def test_lying_small_content_length_is_not_the_middlewares_concern(self, client):
        # Only the declared length is checked; a malformed header must not crash it.
        r = client.post("/api/x", content=b"abc", headers={"content-length": "nope"})
        assert r.status_code != 500

    def test_chunked_body_without_content_length_passes_through(self, client):
        def gen():
            yield b"x" * 50

        r = client.post("/api/x", content=gen())
        assert r.status_code == 200

    def test_extract_content_length(self):
        extract = body_limit_config._extract_content_length
        assert extract({"headers": [(b"Content-Length", b"42")]}) == 42
        assert extract({"headers": [(b"content-length", b"abc")]}) is None
        assert extract({"headers": []}) is None
        assert extract({}) is None


class TestRequestId:
    @pytest.fixture
    def client(self):
        seen_request_ids.clear()
        return _app(RequestIdMiddleware)

    def test_generates_id_when_absent_and_exposes_it_in_context(self, client):
        r = client.get("/api/x")
        rid = r.headers["x-request-id"]
        assert len(rid) == 32
        assert seen_request_ids == [rid]

    def test_reuses_valid_client_id(self, client):
        r = client.get("/api/x", headers={"X-Request-ID": "abc-123"})
        assert r.headers["x-request-id"] == "abc-123"
        assert seen_request_ids == ["abc-123"]

    def test_ids_are_unique_per_request(self, client):
        a = client.get("/api/x").headers["x-request-id"]
        b = client.get("/api/x").headers["x-request-id"]
        assert a != b

    def test_overlong_client_id_is_replaced(self, client):
        long_id = "a" * (MAX_REQUEST_ID_LENGTH + 1)
        r = client.get("/api/x", headers={"X-Request-ID": long_id})
        assert r.headers["x-request-id"] != long_id
        assert len(r.headers["x-request-id"]) == 32

    def test_non_printable_client_id_is_replaced_to_prevent_log_injection(self):
        scope = {"headers": [(b"x-request-id", b"evil\nFAKE LOG LINE")]}
        assert request_id_config._extract_and_validate_request_id(scope) is None
        scope = {"headers": [(b"x-request-id", b"tab\there")]}
        assert request_id_config._extract_and_validate_request_id(scope) is None

    def test_log_filter_injects_current_id_or_dash(self):
        record = logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)
        token = request_id_ctx.set(None)
        try:
            assert RequestIdLogFilter().filter(record) is True
            assert record.request_id == "-"
            request_id_ctx.set("rid-1")
            RequestIdLogFilter().filter(record)
            assert record.request_id == "rid-1"
        finally:
            request_id_ctx.reset(token)


class TestSecurityHeaders:
    @pytest.fixture
    def make_client(self, monkeypatch):
        def _make(environment="development"):
            monkeypatch.setattr(security_config.settings, "environment", environment)
            return _app(SecurityHeadersMiddleware)

        return _make

    def test_base_headers_and_strict_csp_on_api(self, make_client):
        r = make_client().get("/api/x")
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert r.headers["x-permitted-cross-domain-policies"] == "none"
        csp = r.headers["content-security-policy"]
        assert "script-src 'self';" in csp
        assert "unsafe-inline" not in csp.split("script-src")[1].split(";")[0]
        assert _csp_sources(csp).isdisjoint({"https://cdn.jsdelivr.net"})
        assert r.headers["cache-control"] == "no-store, max-age=0"
        assert r.headers["pragma"] == "no-cache"

    @pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
    def test_docs_pages_get_relaxed_csp(self, make_client, path):
        csp = make_client().get(path).headers["content-security-policy"]
        assert _csp_sources(csp) >= {"https://cdn.jsdelivr.net"}

    @pytest.mark.parametrize("path", ["/static/a.js", "/feedicons/a.png"])
    def test_static_assets_are_cacheable(self, make_client, path):
        r = make_client().get(path)
        assert "cache-control" not in r.headers
        assert "pragma" not in r.headers
        assert "content-security-policy" in r.headers

    def test_hsts_only_in_production(self, make_client):
        assert "strict-transport-security" not in make_client("development").get("/api/x").headers
        prod = make_client("production").get("/api/x")
        assert prod.headers["strict-transport-security"].startswith("max-age=31536000")


def test_non_http_scopes_pass_through_untouched():
    """Lifespan/websocket scopes must reach the app unmodified by every middleware."""
    import asyncio

    received = []

    async def inner(scope, receive, send):
        received.append(scope["type"])

    for mw in (RequestBodyLimitMiddleware, RequestIdMiddleware, SecurityHeadersMiddleware):
        asyncio.run(mw(inner)({"type": "lifespan"}, None, None))
    assert received == ["lifespan"] * 3
