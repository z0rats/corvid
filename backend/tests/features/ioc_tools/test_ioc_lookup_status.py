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


# Captured before the autouse fixture below stubs it out, so tests that exercise pacing
# directly can restore the real implementation.
_real_apply_rate_limit = engine.apply_rate_limit


@pytest.fixture(autouse=True)
def _skip_registry_init(monkeypatch):
    """lookup_ioc() always calls this first; the real registry isn't needed for these tests."""
    monkeypatch.setattr(engine, "_ensure_registry_initialized", _async_return(None))
    # Skip real pacing/backoff delays; status-mapping tests don't care about timing.
    monkeypatch.setattr(engine, "apply_rate_limit", _async_return(None))
    monkeypatch.setattr(engine, "_sleep_before_retry", _async_return(None))


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


class TestApplyRateLimitPacesPerService:
    """apply_rate_limit() must sleep just long enough to keep a service within its configured
    requests/sec, and not sleep at all once enough time has already passed."""

    def test_sleeps_for_remaining_interval_when_called_too_soon(self, monkeypatch):
        monkeypatch.setattr(engine, "apply_rate_limit", _real_apply_rate_limit)
        engine.reset_rate_limiters()
        engine._rate_limiters["svc"]["last_request"] = 100.0
        monkeypatch.setattr(engine, "get_service_rate_limit", lambda name: 2.0)  # 0.5s interval
        monkeypatch.setattr(engine.time, "time", lambda: 100.1)

        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(engine.asyncio, "sleep", fake_sleep)

        _run(engine.apply_rate_limit("svc"))

        assert sleeps == [pytest.approx(0.4)]
        assert engine._rate_limiters["svc"]["last_request"] == pytest.approx(100.1)
        assert engine._rate_limiters["svc"]["request_count"] == 1

    def test_no_sleep_once_interval_has_elapsed(self, monkeypatch):
        monkeypatch.setattr(engine, "apply_rate_limit", _real_apply_rate_limit)
        engine.reset_rate_limiters()
        engine._rate_limiters["svc"]["last_request"] = 100.0
        monkeypatch.setattr(engine, "get_service_rate_limit", lambda name: 2.0)  # 0.5s interval
        monkeypatch.setattr(engine.time, "time", lambda: 101.0)

        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(engine.asyncio, "sleep", fake_sleep)

        _run(engine.apply_rate_limit("svc"))

        assert sleeps == []


class TestCallServiceWithRetryBacksOffOnRateLimit:
    """_call_service_with_retry() must retry ServiceRateLimitError with exponential backoff
    (using RETRY_CONFIG), but must not retry other error types."""

    @staticmethod
    def _retry_config(max_retries=3, base_delay=1.0, backoff_factor=2.0, max_delay=30.0):
        return {
            "max_retries": max_retries,
            "base_delay": base_delay,
            "backoff_factor": backoff_factor,
            "max_delay": max_delay,
        }

    def test_retries_then_succeeds_with_growing_backoff(self, monkeypatch):
        monkeypatch.setattr(engine, "get_retry_config", lambda: self._retry_config())
        pacing_calls = []
        sleeps = []

        async def fake_apply(service_name):
            pacing_calls.append(service_name)

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        monkeypatch.setattr(engine, "apply_rate_limit", fake_apply)
        monkeypatch.setattr(engine, "_sleep_before_retry", fake_sleep)

        attempts = {"n": 0}

        async def flaky_func(**kwargs):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise ServiceRateLimitError("svc", "rate limited")
            return {"ok": True}

        result = _run(engine._call_service_with_retry({"func": flaky_func}, {}, "svc"))

        assert result == {"ok": True}
        assert attempts["n"] == 3
        assert sleeps == [1.0, 2.0]
        assert pacing_calls == ["svc", "svc", "svc"]

    def test_raises_rate_limit_error_once_retries_are_exhausted(self, monkeypatch):
        monkeypatch.setattr(engine, "get_retry_config", lambda: self._retry_config(max_retries=2))
        monkeypatch.setattr(engine, "apply_rate_limit", _async_return(None))
        monkeypatch.setattr(engine, "_sleep_before_retry", _async_return(None))

        attempts = {"n": 0}

        async def always_rate_limited(**kwargs):
            attempts["n"] += 1
            raise ServiceRateLimitError("svc", "rate limited")

        with pytest.raises(ServiceRateLimitError):
            _run(engine._call_service_with_retry({"func": always_rate_limited}, {}, "svc"))

        assert attempts["n"] == 3  # initial attempt + 2 retries

    def test_non_rate_limit_errors_are_not_retried(self, monkeypatch):
        monkeypatch.setattr(engine, "apply_rate_limit", _async_return(None))
        attempts = {"n": 0}

        async def failing(**kwargs):
            attempts["n"] += 1
            raise ServiceAuthError("svc", "bad key")

        with pytest.raises(ServiceAuthError):
            _run(engine._call_service_with_retry({"func": failing}, {}, "svc"))

        assert attempts["n"] == 1


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

        async def fake_lookup_ioc(*args, **kwargs):
            return LookupResult(ioc="1.2.3.4", service="svc", status=LookupStatus.SUCCESS, data={"x": 1})

        monkeypatch.setattr(bulk_service, "lookup_ioc", fake_lookup_ioc)

        result = _run(bulk_service.run_single_lookup_with_rate_limit(
            "svc", "1.2.3.4", "ipv4", db=None, semaphore=semaphore,
        ))

        assert result["status"] == LookupStatus.SUCCESS.value
        assert result["data"] == {"x": 1}
