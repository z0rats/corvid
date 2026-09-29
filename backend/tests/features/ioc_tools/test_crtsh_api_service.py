"""Uses httpx.MockTransport (stdlib to httpx, no extra dependency) rather than
mocking away httpx.AsyncClient's behavior, so raise_for_status()/response.json()
parsing in fetch_crtsh_certificates runs for real against a canned response."""

import asyncio

import httpx

from app.features.ioc_tools.domain_finder.service.crtsh_api_service import fetch_crtsh_certificates


def _run(coro):
    return asyncio.run(coro)


def test_returns_parsed_certificate_list_on_success(patch_httpx_transport):
    certs = [
        {"id": 1, "name_value": "www.example.com"},
        {"id": 2, "name_value": "mail.example.com"},
    ]

    def handler(request):
        assert request.url.params["q"] == "%.example.com"
        return httpx.Response(200, json=certs)

    patch_httpx_transport(handler)

    result = _run(fetch_crtsh_certificates("example.com"))

    assert result == certs


def test_returns_empty_list_for_empty_response_body(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, content=b""))

    assert _run(fetch_crtsh_certificates("example.com")) == []
