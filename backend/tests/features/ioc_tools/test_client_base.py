import asyncio

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import client_base
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
    ServiceRateLimitError,
    ServiceUnavailableError,
    _extract_error_detail,
    _require_apikey,
    _require_credentials,
    close_client,
    get_client,
    handle_response,
)


def _run(coro):
    return asyncio.run(coro)


def _response(status_code: int, *, json=None, text=None, headers=None) -> httpx.Response:
    request = httpx.Request("GET", "https://service.example/api")
    kwargs = {"headers": headers or {}}
    if json is not None:
        kwargs["json"] = json
    elif text is not None:
        kwargs["text"] = text
    return httpx.Response(status_code, request=request, **kwargs)


# --- ServiceError hierarchy ------------------------------------------------


def test_service_error_carries_service_name_message_and_status_code():
    err = ServiceError("VirusTotal", "boom", status_code=418)
    assert err.service_name == "VirusTotal"
    assert err.message == "boom"
    assert err.status_code == 418
    assert str(err) == "boom"


def test_service_auth_error_defaults_to_401():
    err = ServiceAuthError("Shodan", "missing key")
    assert err.status_code == 401


def test_service_rate_limit_error_defaults_to_429_and_carries_retry_after():
    err = ServiceRateLimitError("Shodan", "slow down", retry_after="30")
    assert err.status_code == 429
    assert err.retry_after == "30"


def test_service_unavailable_error_defaults_to_503():
    err = ServiceUnavailableError("Shodan", "down")
    assert err.status_code == 503


# --- _extract_error_detail ---------------------------------------------


def test_extract_error_detail_prefers_errors_list_detail():
    response = _response(400, json={"errors": [{"detail": "bad ip"}]})
    assert _extract_error_detail(response, "default") == "bad ip"


def test_extract_error_detail_falls_back_to_message_field():
    response = _response(400, json={"message": "quota exceeded"})
    assert _extract_error_detail(response, "default") == "quota exceeded"


def test_extract_error_detail_falls_back_to_error_string_field():
    response = _response(400, json={"error": "invalid request"})
    assert _extract_error_detail(response, "default") == "invalid request"


def test_extract_error_detail_ignores_non_string_error_field():
    response = _response(400, json={"error": {"code": 5}})
    assert _extract_error_detail(response, "default") == "default"


def test_extract_error_detail_uses_response_text_for_non_json_content():
    response = _response(400, text="plain text error")
    assert _extract_error_detail(response, "default") == "plain text error"


def test_extract_error_detail_returns_default_for_empty_body():
    response = _response(400, text="")
    assert _extract_error_detail(response, "default") == "default"

    response = _response(400, json={"unrelated": "field"})
    assert _extract_error_detail(response, "default") == "default"


# --- handle_response ---------------------------------------------------


class TestHandleResponse:
    def test_returns_parsed_json_on_success(self):
        response = _response(200, json={"ok": True})
        assert _run(handle_response("VirusTotal", response)) == {"ok": True}

    def test_raises_rate_limit_error_on_429(self):
        response = _response(429, json={}, headers={"Retry-After": "60"})
        with pytest.raises(ServiceRateLimitError) as exc_info:
            _run(handle_response("Shodan", response))
        assert exc_info.value.retry_after == "60"
        assert exc_info.value.status_code == 429

    def test_rate_limit_retry_after_defaults_to_unknown(self):
        response = _response(429, json={})
        with pytest.raises(ServiceRateLimitError) as exc_info:
            _run(handle_response("Shodan", response))
        assert exc_info.value.retry_after == "unknown"

    def test_raises_service_error_with_extracted_detail_on_other_http_errors(self):
        response = _response(404, json={"message": "not found"})
        with pytest.raises(ServiceError) as exc_info:
            _run(handle_response("VirusTotal", response))
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.message

    def test_success_status_but_invalid_json_body_raises_service_error(self):
        response = _response(200, text="not json")
        with pytest.raises(ServiceError):
            _run(handle_response("VirusTotal", response))


# --- _require_apikey / _require_credentials -----------------------------


def test_require_apikey_passes_for_non_empty_key():
    _require_apikey("VirusTotal", "some-key")  # must not raise


def test_require_apikey_raises_for_empty_key():
    with pytest.raises(ServiceAuthError):
        _require_apikey("VirusTotal", "")


def test_require_apikey_raises_for_none_key():
    with pytest.raises(ServiceAuthError):
        _require_apikey("VirusTotal", None)


def test_require_credentials_passes_when_all_present():
    _require_credentials("Service", user="a", password="b")  # must not raise


def test_require_credentials_raises_when_any_missing():
    with pytest.raises(ServiceAuthError):
        _require_credentials("Service", user="a", password="")


def test_require_credentials_with_zero_credentials_does_not_raise():
    # all() of an empty collection is vacuously True, so calling with no
    # credentials at all passes rather than raising - only an *empty value*
    # among named credentials trips the check, not the absence of any.
    _require_credentials("Service")


# --- shared client lifecycle ---------------------------------------------


class TestSharedClientLifecycle:
    def test_get_client_returns_same_instance_on_repeated_calls(self):
        async def _scenario():
            client_a = get_client()
            client_b = get_client()
            return client_a is client_b

        try:
            assert _run(_scenario()) is True
        finally:
            _run(close_client())

    def test_get_client_creates_new_instance_after_close(self):
        async def _scenario():
            client_a = get_client()
            await close_client()
            client_b = get_client()
            return client_a is not client_b

        try:
            assert _run(_scenario()) is True
        finally:
            _run(close_client())

    def test_close_client_is_idempotent(self):
        _run(close_client())
        _run(close_client())
        assert client_base._shared_client is None
