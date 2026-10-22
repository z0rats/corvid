"""Cert Spotter client: the request it sends, one-page truncation and its rate-limit error.
Drift vs empty is pinned by `test_domain_provider_contract.py`."""

import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.service.certspotter_api_service import (
    fetch_certspotter_issuances,
)

ISSUANCE = {"id": "1", "dns_names": ["example.com", "www.example.com"]}
NEXT_LINK = '<https://api.certspotter.com/issuances?after=1&domain=example.com>; rel="next"'


def _fetch(patch_httpx_transport, response: httpx.Response, seen: list | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return response

    patch_httpx_transport(handler)
    return asyncio.run(fetch_certspotter_issuances("example.com"))


def test_requests_one_page_of_issuances_with_subdomains_and_dns_names(patch_httpx_transport):
    seen = []
    _fetch(patch_httpx_transport, httpx.Response(200, json=[ISSUANCE]), seen)

    (request,) = seen
    assert request.url.host == "api.certspotter.com"
    assert request.url.path == "/v1/issuances"
    assert dict(request.url.params) == {
        "domain": "example.com",
        "include_subdomains": "true",
        "expand": "dns_names",
    }


def test_a_single_page_is_not_truncated(patch_httpx_transport):
    page = _fetch(patch_httpx_transport, httpx.Response(200, json=[ISSUANCE]))

    assert page.issuances == [ISSUANCE]
    assert page.truncated is False


def test_a_next_link_marks_the_page_truncated(patch_httpx_transport):
    response = httpx.Response(200, json=[ISSUANCE], headers={"Link": NEXT_LINK})

    assert _fetch(patch_httpx_transport, response).truncated is True


def test_429_is_rate_limited(patch_httpx_transport):
    with pytest.raises(AppHTTPException) as caught:
        _fetch(patch_httpx_transport, httpx.Response(429, json={"code": "rate_limited"}))

    assert caught.value.status_code == 429
    assert caught.value.error_code == "CERTSPOTTER_RATE_LIMITED"


def test_other_http_errors_are_api_errors(patch_httpx_transport):
    response = httpx.Response(403, json={"code": "not_allowed_by_plan", "message": "x"})

    with pytest.raises(AppHTTPException) as caught:
        _fetch(patch_httpx_transport, response)

    assert caught.value.error_code == "CERTSPOTTER_API_ERROR"
