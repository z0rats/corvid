"""The canary outcome policy (`tests/canary/policy.py`), pinned in the normal suite: which live-call
failures skip (the source didn't answer us) and which fail (it changed, or now demands a key)."""

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
    ServiceRateLimitError,
    ServiceUnavailableError,
)
from tests.canary import policy

SKIP, FAIL, RAISE = "skip", "fail", "raise"


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://source.example/api")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


def _app(status: int, code: str) -> AppHTTPException:
    return AppHTTPException(status_code=status, detail="detail", error_code=code)


CASES = [
    # network
    (httpx.ConnectTimeout("timed out"), SKIP),
    (httpx.ConnectError("refused"), SKIP),
    (ConnectionResetError("reset"), SKIP),
    # raw HTTP statuses
    (_status_error(401), FAIL),
    (_status_error(403), SKIP),
    (_status_error(404), RAISE),
    (_status_error(429), SKIP),
    (_status_error(451), SKIP),
    (_status_error(503), SKIP),
    (_status_error(400), RAISE),
    # ioc_lookup's client_base
    (ServiceAuthError("svc", "bad key"), FAIL),
    (ServiceRateLimitError("svc", "slow down"), SKIP),
    (ServiceUnavailableError("svc", "down"), SKIP),
    (ServiceError("svc", "forbidden", status_code=403), SKIP),
    (ServiceError("svc", "server", status_code=500), SKIP),
    (ServiceError("svc", "not found", status_code=404), RAISE),
    # domain_finder's provider_http
    (_app(504, "CRTSH_TIMEOUT"), SKIP),
    (_app(503, "RAPIDDNS_CONNECTION_ERROR"), SKIP),
    (_app(429, "HACKERTARGET_RATE_LIMITED"), SKIP),
    (_app(401, "WAYBACK_API_ERROR"), FAIL),
    (_app(403, "URLSCAN_API_ERROR"), SKIP),
    (_app(502, "RDAP_API_ERROR"), SKIP),
    (_app(404, "RAPIDDNS_API_ERROR"), RAISE),
    (_app(502, "CRTSH_INVALID_RESPONSE"), RAISE),
    (_app(500, "WAYBACK_UNEXPECTED_ERROR"), RAISE),
    (_app(404, "RDAP_NOT_FOUND"), RAISE),
    # ru_business_check's Russian ValueErrors
    (ValueError("ЕГРЮЛ недоступен: HTTP 503"), SKIP),
    (ValueError("Сайт ограничил доступ (HTTP 451)"), SKIP),
    (ValueError("Требуется капча"), SKIP),
    (ValueError("ЕГРЮЛ: схема ответа изменилась"), RAISE),
    (ValueError("Ничего не найдено"), RAISE),
    # anything else
    (KeyError("info"), RAISE),
    (AssertionError("drift"), RAISE),
]


@pytest.mark.parametrize(("exc", "outcome"), CASES, ids=[repr(c[0])[:60] for c in CASES])
def test_skip_or_raise(exc, outcome):
    expected = {
        SKIP: pytest.skip.Exception,
        FAIL: pytest.fail.Exception,
        RAISE: type(exc),
    }[outcome]
    with pytest.raises(expected) as caught:
        policy.skip_or_raise(exc)
    if outcome == RAISE:
        assert caught.value is exc


def test_live_returns_the_result_and_applies_the_policy():
    async def ok():
        return 42

    async def unreachable():
        raise httpx.ReadTimeout("slow")

    assert policy.live(ok()) == 42
    with pytest.raises(pytest.skip.Exception):
        policy.live(unreachable())


def test_get_fails_on_a_redirect_it_was_not_told_to_follow(monkeypatch):
    request = httpx.Request("GET", "https://source.example/api")
    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kw: httpx.Response(301, request=request, headers={"location": "/x"}),
    )
    with pytest.raises(httpx.HTTPStatusError):
        policy.get("https://source.example/api")


def test_json_body_fails_on_html():
    response = httpx.Response(200, text="<html>overloaded</html>")
    with pytest.raises(pytest.fail.Exception, match="expected JSON"):
        policy.json_body(response)
