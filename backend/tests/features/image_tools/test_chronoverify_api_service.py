import asyncio

import httpx
import pytest

from app.features.image_tools.service import chronoverify_api_service


def _run(coro):
    return asyncio.run(coro)


class TestFetchChronoverifyVerdict:
    def test_sends_bearer_header_when_key_provided(self, monkeypatch):
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["auth"] = request.headers.get("Authorization")
            return httpx.Response(200, json={"verdict": "consistent"})

        original_client = httpx.AsyncClient

        def fake_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return original_client(*args, **kwargs)

        monkeypatch.setattr(chronoverify_api_service.httpx, "AsyncClient", fake_client)

        result = _run(
            chronoverify_api_service.fetch_chronoverify_verdict("photo.jpg", b"data", "cv_live_x")
        )

        assert result == {"verdict": "consistent"}
        assert captured["auth"] == "Bearer cv_live_x"

    def test_no_auth_header_when_keyless(self, monkeypatch):
        captured = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["auth"] = request.headers.get("Authorization")
            return httpx.Response(200, json={"verdict": "inconclusive"})

        original_client = httpx.AsyncClient

        def fake_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return original_client(*args, **kwargs)

        monkeypatch.setattr(chronoverify_api_service.httpx, "AsyncClient", fake_client)

        _run(chronoverify_api_service.fetch_chronoverify_verdict("photo.jpg", b"data", None))

        assert captured["auth"] is None

    @pytest.mark.parametrize("status_code", [413, 415, 429, 401])
    def test_known_error_statuses_raise_value_error(self, monkeypatch, status_code):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code, json={})

        original_client = httpx.AsyncClient

        def fake_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return original_client(*args, **kwargs)

        monkeypatch.setattr(chronoverify_api_service.httpx, "AsyncClient", fake_client)

        with pytest.raises(ValueError):
            _run(chronoverify_api_service.fetch_chronoverify_verdict("photo.jpg", b"data", None))

    def test_server_error_raises_http_status_error(self, monkeypatch):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={})

        original_client = httpx.AsyncClient

        def fake_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return original_client(*args, **kwargs)

        monkeypatch.setattr(chronoverify_api_service.httpx, "AsyncClient", fake_client)

        with pytest.raises(httpx.HTTPStatusError):
            _run(chronoverify_api_service.fetch_chronoverify_verdict("photo.jpg", b"data", None))
