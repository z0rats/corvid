"""Uses httpx.MockTransport (stdlib to httpx, no extra dependency) rather than
mocking away httpx.AsyncClient's behavior, so raise_for_status()/response.json()
parsing in fetch_wayback_snapshots runs for real against a canned response."""

import asyncio

import httpx

from app.features.ioc_tools.domain_finder.service.wayback_api_service import (
    fetch_wayback_snapshots,
)

CDX_ROWS = [
    ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"],
    [
        "com,example)/",
        "20200101000000",
        "http://example.com/",
        "text/html",
        "200",
        "ABC123",
        "1024",
    ],
    [
        "com,example)/",
        "20260730120433",
        "http://example.com/",
        "text/html",
        "200",
        "DEF456",
        "2048",
    ],
]


def _run(coro):
    return asyncio.run(coro)


def test_returns_parsed_capture_list_on_success(patch_httpx_transport):
    def handler(request):
        assert request.url.params["url"] == "example.com"
        assert request.url.params["matchType"] == "domain"
        # Negative limit - most recent captures, not the oldest ones
        assert request.url.params["limit"] == "-200"
        return httpx.Response(200, json=CDX_ROWS)

    patch_httpx_transport(handler)

    result = _run(fetch_wayback_snapshots("example.com"))

    assert len(result) == 2
    assert result[0]["timestamp"] == "20200101000000"
    assert result[0]["original"] == "http://example.com/"
    assert result[1]["statuscode"] == "200"


def test_narrows_to_exact_page_when_path_given(patch_httpx_transport):
    def handler(request):
        assert request.url.params["url"] == "example.com/login"
        assert "matchType" not in request.url.params
        return httpx.Response(200, json=CDX_ROWS)

    patch_httpx_transport(handler)

    result = _run(fetch_wayback_snapshots("example.com", "/login"))

    assert len(result) == 2


def test_returns_empty_list_for_header_only_response(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, json=[CDX_ROWS[0]]))

    assert _run(fetch_wayback_snapshots("doesnotexist.example")) == []


def test_returns_empty_list_for_empty_array_response(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, json=[]))

    assert _run(fetch_wayback_snapshots("doesnotexist.example")) == []


def test_returns_empty_list_for_empty_response_body(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, content=b""))

    assert _run(fetch_wayback_snapshots("example.com")) == []
