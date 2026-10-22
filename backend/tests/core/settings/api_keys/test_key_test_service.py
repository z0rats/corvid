"""Live API key tests (key_test_clients.py / key_test_service.py) against canned responses."""

import base64
import logging

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_read_db
from app.core.settings.api_keys.config.service_config import SERVICE_DEFINITIONS
from app.core.settings.api_keys.routers import key_test_routes
from app.core.settings.api_keys.schemas.key_test_schemas import KeyTestStatus
from app.core.settings.api_keys.service import key_test_service
from app.core.settings.api_keys.service.key_test_clients import KEY_TESTS
from tests.conftest import run

SECRET = "sekr1t-key-value-0123456789"


class _Key:
    def __init__(self, key):
        self.key = key

    def is_configured(self):
        return bool(self.key)


@pytest.fixture
def saved_keys(monkeypatch):
    """Every key name resolves to SECRET unless listed in the returned `missing` set."""
    missing: set[str] = set()

    async def fake_get_apikey(db, name):
        return None if name in missing else _Key(SECRET)

    monkeypatch.setattr(key_test_service, "get_apikey", fake_get_apikey)
    return missing


@pytest.fixture
def respond(patch_httpx_transport):
    """Routes every provider call to `handler`; returns the list of requests seen."""
    seen: list[httpx.Request] = []

    def _install(handler):
        def wrapped(request):
            seen.append(request)
            return handler(request)

        patch_httpx_transport(wrapped)
        return seen

    return _install


def _test(service):
    return run(key_test_service.run_key_test(None, service))


@pytest.mark.parametrize("service", sorted(KEY_TESTS))
@pytest.mark.parametrize(
    ("code", "expected"),
    [
        (200, KeyTestStatus.OK),
        (401, KeyTestStatus.REJECTED),
        (403, KeyTestStatus.REJECTED),
        (402, KeyTestStatus.PLAN_REQUIRED),
        (429, KeyTestStatus.RATE_LIMITED),
        (500, KeyTestStatus.ERROR),
    ],
)
def test_http_status_maps_to_a_key_status(service, code, expected, saved_keys, respond):
    respond(lambda request: httpx.Response(code, json={"echo": SECRET}))

    result = _test(service)

    assert result.status is expected
    assert result.http_status == code
    assert SECRET not in result.model_dump_json()


@pytest.mark.parametrize("service", sorted(KEY_TESTS))
def test_network_failure_is_unreachable(service, saved_keys, respond):
    def boom(request):
        raise httpx.ConnectTimeout(f"timed out: {request.url}", request=request)

    respond(boom)

    result = _test(service)

    assert result.status is KeyTestStatus.UNREACHABLE
    assert SECRET not in result.model_dump_json()


@pytest.mark.parametrize("service", sorted(KEY_TESTS))
@pytest.mark.parametrize(
    "failure",
    [
        lambda request: httpx.ConnectError(f"failed: {request.url}", request=request),
        lambda request: RuntimeError(f"boom at {request.url} {request.headers}"),
    ],
    ids=["network", "unexpected"],
)
def test_failures_never_log_the_key(service, failure, saved_keys, respond, caplog):
    def raise_failure(request):
        raise failure(request)

    respond(raise_failure)

    with caplog.at_level(logging.DEBUG):
        _test(service)

    logged = caplog.text + "".join(str(r.exc_info) for r in caplog.records if r.exc_info)
    assert SECRET not in logged
    assert service in caplog.text


@pytest.mark.parametrize("service", sorted(KEY_TESTS))
def test_check_sends_the_saved_key(service, saved_keys, respond):
    seen = respond(lambda request: httpx.Response(200, json={}))

    _test(service)

    request = seen[0]
    sent = str(request.url) + str(dict(request.headers)) + request.content.decode()
    if "authorization" in request.headers and request.headers["authorization"].startswith("Basic"):
        sent += base64.b64decode(request.headers["authorization"][6:]).decode()
    assert SECRET in sent
    assert request.url.scheme == "https"


def test_virustotal_reports_daily_quota(saved_keys, respond):
    respond(
        lambda request: httpx.Response(
            200,
            json={
                "data": {
                    "attributes": {"quotas": {"api_requests_daily": {"used": 3, "allowed": 500}}}
                }
            },
        )
    )

    quota = _test("virustotal").quota

    assert (quota.used, quota.limit, quota.remaining, quota.period) == (3, 500, 497, "daily")


def test_shodan_reports_credits_only(saved_keys, respond):
    respond(lambda request: httpx.Response(200, json={"query_credits": 42}))

    quota = _test("shodan").quota

    assert (quota.used, quota.limit, quota.remaining) == (None, None, 42)


def test_hunter_reports_monthly_searches(saved_keys, respond):
    respond(
        lambda request: httpx.Response(
            200, json={"data": {"requests": {"searches": {"used": 10, "available": 15}}}}
        )
    )

    quota = _test("hunterio").quota

    assert (quota.used, quota.limit, quota.remaining, quota.period) == (10, 25, 15, "monthly")


def test_github_reports_hourly_rate_limit(saved_keys, respond):
    respond(
        lambda request: httpx.Response(
            200, json={"resources": {"core": {"limit": 5000, "used": 1, "remaining": 4999}}}
        )
    )

    quota = _test("github").quota

    assert (quota.limit, quota.remaining, quota.period) == (5000, 4999, "hourly")


def test_quota_is_dropped_when_the_key_is_rejected(saved_keys, respond):
    respond(lambda request: httpx.Response(401, json={"query_credits": 42}))

    assert _test("shodan").quota is None


def test_missing_quota_fields_still_pass(saved_keys, respond):
    respond(lambda request: httpx.Response(200, text="not json"))

    result = _test("virustotal")

    assert result.status is KeyTestStatus.OK
    assert result.quota.remaining is None


def test_ipqualityscore_bad_key_is_a_200_with_success_false(saved_keys, respond):
    respond(
        lambda request: httpx.Response(
            200, json={"success": False, "message": "Invalid or unauthorized key."}
        )
    )

    assert _test("ipqualityscore").status is KeyTestStatus.REJECTED


def test_ipqualityscore_other_failure_is_an_error(saved_keys, respond):
    respond(lambda request: httpx.Response(200, json={"success": False, "message": "Down."}))

    assert _test("ipqualityscore").status is KeyTestStatus.ERROR


def test_ipqualityscore_reports_credits(saved_keys, respond):
    respond(
        lambda request: httpx.Response(200, json={"success": True, "credits": 900, "usage": 100})
    )

    quota = _test("ipqualityscore").quota

    assert (quota.used, quota.remaining) == (100, 900)


def test_nvd_404_means_rejected_key(saved_keys, respond):
    respond(lambda request: httpx.Response(404))

    assert _test("nistnvd").status is KeyTestStatus.REJECTED


def test_mandiant_sends_basic_auth(saved_keys, respond):
    seen = respond(lambda request: httpx.Response(200, json={"access_token": "t"}))

    _test("mandiant")

    assert seen[0].headers["authorization"].startswith("Basic ")


def test_exempt_service_is_untestable_without_a_request(saved_keys, respond):
    seen = respond(lambda request: httpx.Response(200))

    result = _test("abuseipdb")

    assert result.status is KeyTestStatus.UNTESTABLE
    assert "daily allowance" in result.detail
    assert seen == []


def test_missing_key_is_not_configured(saved_keys, respond):
    saved_keys.add("crowdstrike_client_secret")
    seen = respond(lambda request: httpx.Response(200))

    assert _test("crowdstrike").status is KeyTestStatus.NOT_CONFIGURED
    assert seen == []


def test_test_all_skips_untestable_and_unconfigured(saved_keys, respond):
    saved_keys.update({"shodan", "abuseipdb"})
    respond(lambda request: httpx.Response(200, json={}))

    results = run(key_test_service.run_all_key_tests(None))

    services = {r.service for r in results}
    assert services == set(KEY_TESTS) - {"shodan"}
    assert all(r.status is KeyTestStatus.OK for r in results)


@pytest.fixture
def client():
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(key_test_routes.router)
    app.dependency_overrides[get_read_db] = lambda: None
    limiter.reset()
    return TestClient(app)


def test_route_tests_one_service(client, saved_keys, respond):
    respond(lambda request: httpx.Response(401))

    response = client.post("/api/services/alienvault/test")

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert SECRET not in response.text


def test_route_404s_an_unknown_or_keyless_service(client, saved_keys):
    assert client.post("/api/services/nope/test").status_code == 404
    keyless = next(k for k, d in SERVICE_DEFINITIONS.items() if not d.required_keys)
    assert client.post(f"/api/services/{keyless}/test").status_code == 404


def test_route_tests_all(client, saved_keys, respond):
    respond(lambda request: httpx.Response(200, json={}))

    response = client.post("/api/services/test")

    assert response.status_code == 200
    assert {r["service"] for r in response.json()} == set(KEY_TESTS)
