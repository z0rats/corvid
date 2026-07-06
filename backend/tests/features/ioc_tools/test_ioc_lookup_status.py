import asyncio

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import LookupResult, LookupStatus
from app.features.ioc_tools.ioc_lookup.single_lookup.service import ioc_lookup_engine as engine
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError, ServiceError, ServiceRateLimitError, ServiceUnavailableError,
)
from app.features.ioc_tools.ioc_lookup.bulk_lookup.service import bulk_ioc_lookup_service as bulk_service


def _run(coro):
    return asyncio.run(coro)


def _async_return(value):
    async def _inner(*args, **kwargs):
        return value
    return _inner


def _service_config(func=None, requires_key=True, ioc_types=("ipv4",)):
    config = {
        "name": "TestService",
        "supported_ioc_types": list(ioc_types),
        "func": func,
    }
    if requires_key:
        config["api_key_name"] = "TEST_API_KEY"
    return config


@pytest.fixture(autouse=True)
def _skip_registry_init(monkeypatch):
    """lookup_ioc() always calls this first; the real registry isn't needed for these tests."""
    monkeypatch.setattr(engine, "_ensure_registry_initialized", _async_return(None))


class TestLookupIocNeverRaisesForExpectedConditions:
    """lookup_ioc() must always return a LookupResult, never raise, for conditions that are
    routine (missing key, unsupported type, rate limit, upstream error, timeout) so bulk-lookup
    callers can read a uniform LookupStatus instead of parsing exception text."""

    def test_missing_api_key_returns_unauthorized(self, monkeypatch):
        monkeypatch.setattr(engine, "get_service", lambda name: _service_config())
        monkeypatch.setattr(engine, "_get_api_keys", _async_return(None))

        result = _run(engine.lookup_ioc("testsvc", "1.2.3.4", "ipv4", db=None))

        assert result.status == LookupStatus.UNAUTHORIZED
        assert result.error

    def test_unsupported_ioc_type_returns_error_not_raise(self, monkeypatch):
        monkeypatch.setattr(engine, "get_service", lambda name: _service_config(ioc_types=("domain",)))

        result = _run(engine.lookup_ioc("testsvc", "1.2.3.4", "ipv4", db=None))

        assert result.status == LookupStatus.ERROR
        assert "ipv4" in result.error

    @pytest.mark.parametrize(
        "raised, expected_status",
        [
            (ServiceRateLimitError("svc", "rate limited"), LookupStatus.RATE_LIMITED),
            (ServiceAuthError("svc", "auth failed"), LookupStatus.UNAUTHORIZED),
            (ServiceUnavailableError("svc", "unavailable"), LookupStatus.SERVICE_UNAVAILABLE),
            (ServiceError("svc", "boom"), LookupStatus.ERROR),
            (httpx.TimeoutException("timed out"), LookupStatus.SERVICE_UNAVAILABLE),
            (httpx.ConnectError("connection refused"), LookupStatus.SERVICE_UNAVAILABLE),
        ],
    )
    def test_service_exceptions_map_to_lookup_status(self, monkeypatch, raised, expected_status):
        async def failing_func(**kwargs):
            raise raised

        monkeypatch.setattr(
            engine, "get_service",
            lambda name: _service_config(func=failing_func, requires_key=False),
        )
        monkeypatch.setattr(engine, "_get_api_keys", _async_return({}))

        result = _run(engine.lookup_ioc("testsvc", "1.2.3.4", "ipv4", db=None))

        assert result.status == expected_status
        assert result.error

    def test_success_returns_success_status(self, monkeypatch):
        async def ok_func(**kwargs):
            return {"foo": "bar"}

        monkeypatch.setattr(
            engine, "get_service",
            lambda name: _service_config(func=ok_func, requires_key=False),
        )
        monkeypatch.setattr(engine, "_get_api_keys", _async_return({}))

        result = _run(engine.lookup_ioc("testsvc", "1.2.3.4", "ipv4", db=None))

        assert result.status == LookupStatus.SUCCESS
        assert result.data == {"foo": "bar"}


class TestRunSingleLookupWithRateLimitStatusIsUniform:
    """The bulk-lookup wrapper must always surface a LookupStatus value under "status",
    for both the pre-checks it does itself and whatever lookup_ioc() returns/raises."""

    @pytest.fixture
    def semaphore(self):
        return asyncio.Semaphore(1)

    def test_service_not_configured_is_error_status(self, monkeypatch, semaphore):
        monkeypatch.setattr(bulk_service, "get_service", lambda name: None)

        result = _run(bulk_service.run_single_lookup_with_rate_limit(
            "unknown", "1.2.3.4", "ipv4", db=None, semaphore=semaphore,
        ))

        assert result["status"] == LookupStatus.ERROR.value
        assert "error" in result

    def test_unsupported_ioc_type_is_error_status(self, monkeypatch, semaphore):
        monkeypatch.setattr(bulk_service, "get_service", lambda name: {"supported_ioc_types": ["domain"]})

        result = _run(bulk_service.run_single_lookup_with_rate_limit(
            "svc", "1.2.3.4", "ipv4", db=None, semaphore=semaphore,
        ))

        assert result["status"] == LookupStatus.ERROR.value

    @pytest.mark.parametrize(
        "lookup_status",
        [
            LookupStatus.RATE_LIMITED,
            LookupStatus.UNAUTHORIZED,
            LookupStatus.SERVICE_UNAVAILABLE,
            LookupStatus.ERROR,
        ],
    )
    def test_engine_status_is_propagated_verbatim(self, monkeypatch, semaphore, lookup_status):
        monkeypatch.setattr(bulk_service, "get_service", lambda name: {"supported_ioc_types": ["ipv4"]})
        monkeypatch.setattr(bulk_service, "apply_rate_limit", _async_return(None))

        async def fake_lookup_ioc(*args, **kwargs):
            return LookupResult(ioc="1.2.3.4", service="svc", status=lookup_status, error="boom")

        monkeypatch.setattr(bulk_service, "lookup_ioc", fake_lookup_ioc)

        result = _run(bulk_service.run_single_lookup_with_rate_limit(
            "svc", "1.2.3.4", "ipv4", db=None, semaphore=semaphore,
        ))

        assert result["status"] == lookup_status.value
        assert result["error"] == "boom"

    def test_unexpected_exception_is_error_status_not_raw_traceback(self, monkeypatch, semaphore):
        monkeypatch.setattr(bulk_service, "get_service", lambda name: {"supported_ioc_types": ["ipv4"]})
        monkeypatch.setattr(bulk_service, "apply_rate_limit", _async_return(None))

        async def boom(*args, **kwargs):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(bulk_service, "lookup_ioc", boom)

        result = _run(bulk_service.run_single_lookup_with_rate_limit(
            "svc", "1.2.3.4", "ipv4", db=None, semaphore=semaphore,
        ))

        assert result["status"] == LookupStatus.ERROR.value
        assert result["error"] == "kaboom"

    def test_success_is_success_status(self, monkeypatch, semaphore):
        monkeypatch.setattr(bulk_service, "get_service", lambda name: {"supported_ioc_types": ["ipv4"]})
        monkeypatch.setattr(bulk_service, "apply_rate_limit", _async_return(None))

        async def fake_lookup_ioc(*args, **kwargs):
            return LookupResult(ioc="1.2.3.4", service="svc", status=LookupStatus.SUCCESS, data={"x": 1})

        monkeypatch.setattr(bulk_service, "lookup_ioc", fake_lookup_ioc)

        result = _run(bulk_service.run_single_lookup_with_rate_limit(
            "svc", "1.2.3.4", "ipv4", db=None, semaphore=semaphore,
        ))

        assert result["status"] == LookupStatus.SUCCESS.value
        assert result["data"] == {"x": 1}
