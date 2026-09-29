"""check_urlhaus: abuse.ch URLhaus lookup by URL (`/v1/url/`) or host (`/v1/host/`).

The API needs an abuse.ch Auth-Key in a request header (unauthenticated calls get a bare
401), and the ThreatFox client shares that header, so both are covered here.
"""

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    external_api_clients,
    service_registry,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.provider_spec import (
    build_call_args,
    validate_provider_spec,
)
from tests.conftest import run as _run


def _response(status_code: int, json=None, text: str | None = None) -> httpx.Response:
    request = httpx.Request("POST", "https://urlhaus-api.abuse.ch/v1/host/")
    if text is not None:
        return httpx.Response(status_code, request=request, text=text)
    return httpx.Response(status_code, request=request, json=json if json is not None else {})


class _FakeClient:
    def __init__(self, response: httpx.Response):
        self._response = response
        self.last_call: dict | None = None

    async def post(self, url, **kwargs):
        self.last_call = {"url": url, **kwargs}
        return self._response


def _patch_client(monkeypatch, response: httpx.Response) -> _FakeClient:
    fake = _FakeClient(response)
    monkeypatch.setattr(external_api_clients, "get_client", lambda: fake)
    return fake


class TestCheckUrlhaus:
    def test_requires_apikey(self):
        with pytest.raises(ServiceAuthError):
            _run(external_api_clients.check_urlhaus("http://evil.example/a", "url", ""))

    def test_url_lookup_posts_to_url_endpoint_with_auth_key_header(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"query_status": "ok"}))

        result = _run(external_api_clients.check_urlhaus("http://evil.example/a", "url", "k-123"))

        assert result == {"query_status": "ok"}
        assert fake.last_call["url"] == "https://urlhaus-api.abuse.ch/v1/url/"
        assert fake.last_call["headers"] == {"Auth-Key": "k-123"}
        assert fake.last_call["data"] == {"url": "http://evil.example/a"}

    def test_host_lookup_posts_to_host_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"query_status": "ok"}))

        _run(external_api_clients.check_urlhaus("evil.example", "host", "k-123"))

        assert fake.last_call["url"] == "https://urlhaus-api.abuse.ch/v1/host/"
        assert fake.last_call["data"] == {"host": "evil.example"}

    def test_no_results_passes_through_as_a_clean_result(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json={"query_status": "no_results"}))

        result = _run(external_api_clients.check_urlhaus("clean.example", "host", "k-123"))

        assert result == {"query_status": "no_results"}

    @pytest.mark.parametrize("status_code", [401, 403])
    def test_rejected_key_raises_auth_error(self, monkeypatch, status_code):
        _patch_client(monkeypatch, _response(status_code, text='{"error": "Unauthorized"}'))

        with pytest.raises(ServiceAuthError):
            _run(external_api_clients.check_urlhaus("evil.example", "host", "bad-key"))

    def test_other_http_errors_still_raise_service_error(self, monkeypatch):
        _patch_client(monkeypatch, _response(500, text="boom"))

        with pytest.raises(ServiceError) as exc_info:
            _run(external_api_clients.check_urlhaus("evil.example", "host", "k-123"))

        assert not isinstance(exc_info.value, ServiceAuthError)


class TestUrlhausProviderSpec:
    @pytest.fixture
    def spec(self):
        service_registry.register_services(external_api_clients)
        return service_registry.get_service("urlhaus")

    def test_spec_matches_function_signature_for_every_supported_type(self, spec):
        validate_provider_spec(spec)

    @pytest.mark.parametrize(
        ("ioc_type", "expected_selector"),
        [("URL", "url"), ("Domain", "host"), ("IPv4", "host")],
    )
    def test_ioc_type_selects_the_query_endpoint(self, spec, ioc_type, expected_selector):
        args = build_call_args(spec, "x", ioc_type, {"urlhaus": "k"})

        assert args == {"ioc": "x", "ioc_type": expected_selector, "apikey": "k"}


class TestThreatfoxAuthHeader:
    def test_sends_abusech_auth_key_header(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"query_status": "no_result"}))

        _run(external_api_clients.check_threatfox("evil.example", "k-123"))

        assert fake.last_call["headers"] == {"Auth-Key": "k-123"}
