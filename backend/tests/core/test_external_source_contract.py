"""The shared source-drift guard and outcome classifier (`core/external_sources/`)."""

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.core.external_sources.contract import (
    SourceDriftError,
    require_dict,
    require_fields,
    require_list_field,
)
from app.core.external_sources.outcome import SourceOutcome, classify
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceDriftError,
    ServiceError,
    ServiceRateLimitError,
    ServiceUnavailableError,
)


class TestContract:
    def test_require_dict_rejects_non_objects(self):
        for bad in (None, [], "x", 1):
            with pytest.raises(SourceDriftError, match="not a JSON object"):
                require_dict(bad, label="L")

    def test_require_list_field_accepts_an_empty_list_but_not_a_missing_or_non_list(self):
        assert require_list_field({"a": []}, "a", label="L") == []
        for bad in ({}, {"a": None}, {"a": "x"}, None):
            with pytest.raises(SourceDriftError):
                require_list_field(bad, "a", label="L")

    def test_require_fields_treats_null_as_present_and_absent_as_drift(self):
        assert require_fields({"a": None}, ("a",), label="L") == {"a": None}
        with pytest.raises(SourceDriftError, match="no field 'b'"):
            require_fields({"a": 1}, ("a", "b"), label="L")

    def test_a_custom_error_class_is_raised_instead(self):
        class MyError(ValueError):
            pass

        with pytest.raises(MyError):
            require_dict([], error=MyError, label="L")

    def test_drift_is_a_value_error_so_provider_errors_still_catches_it(self):
        assert issubclass(SourceDriftError, ValueError)


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://source.example/api")
    return httpx.HTTPStatusError(
        f"HTTP {status}", request=request, response=httpx.Response(status, request=request)
    )


def _app(status: int, code: str) -> AppHTTPException:
    return AppHTTPException(status_code=status, detail="detail", error_code=code)


U, B, A, D = (
    SourceOutcome.UNREACHABLE,
    SourceOutcome.BLOCKED,
    SourceOutcome.AUTH,
    SourceOutcome.DRIFT,
)

CASES = [
    (httpx.ConnectTimeout("timed out"), U),
    (ConnectionResetError("reset"), U),
    (_status_error(401), A),
    (_status_error(403), B),
    (_status_error(429), B),
    (_status_error(503), U),
    (_status_error(404), D),
    (ServiceAuthError("svc", "bad key"), A),
    (ServiceRateLimitError("svc", "slow down"), B),
    (ServiceUnavailableError("svc", "down"), U),
    (ServiceError("svc", "forbidden", status_code=403), B),
    (ServiceError("svc", "not found", status_code=404), D),
    (ServiceDriftError("svc", "no 'data'"), D),
    (_app(504, "CRTSH_TIMEOUT"), U),
    (_app(503, "RAPIDDNS_CONNECTION_ERROR"), U),
    (_app(429, "HACKERTARGET_RATE_LIMITED"), B),
    (_app(401, "WAYBACK_API_ERROR"), A),
    (_app(403, "URLSCAN_API_ERROR"), B),
    (_app(502, "RDAP_API_ERROR"), U),
    (_app(404, "RAPIDDNS_API_ERROR"), D),
    (_app(502, "CRTSH_INVALID_RESPONSE"), D),
    (_app(502, "CRTSH_SCHEMA_DRIFT"), D),
    (_app(500, "WAYBACK_UNEXPECTED_ERROR"), D),
    (SourceDriftError("changed"), D),
    (ValueError("ЕГРЮЛ недоступен: HTTP 503"), B),
    (ValueError("Требуется капча"), B),
    (ValueError("ЕГРЮЛ: схема ответа изменилась"), D),
    (ValueError("Ничего не найдено"), D),
    (KeyError("info"), D),
]


@pytest.mark.parametrize(("exc", "outcome"), CASES, ids=[repr(c[0])[:60] for c in CASES])
def test_classify(exc, outcome):
    assert classify(exc) is outcome


def test_classify_never_reports_a_result_state_for_an_error():
    assert {classify(exc) for exc, _ in CASES}.isdisjoint({SourceOutcome.OK, SourceOutcome.EMPTY})
