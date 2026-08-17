import asyncio

import httpx
import pytest

from app.features.image_tools.service import reverse_geocode_service


def _run(coro):
    return asyncio.run(coro)


class TestReverseGeocode:
    def test_returns_display_name_on_success(self, monkeypatch):
        async def fake_fetch(latitude, longitude):
            return {"display_name": "10 Downing Street, London, UK"}

        monkeypatch.setattr(reverse_geocode_service, "_fetch_nominatim", fake_fetch)

        address = _run(reverse_geocode_service.reverse_geocode(51.5034, -0.1276))

        assert address == "10 Downing Street, London, UK"

    def test_returns_none_when_display_name_missing(self, monkeypatch):
        async def fake_fetch(latitude, longitude):
            return {}

        monkeypatch.setattr(reverse_geocode_service, "_fetch_nominatim", fake_fetch)

        assert _run(reverse_geocode_service.reverse_geocode(0, 0)) is None

    def test_returns_none_on_timeout(self, monkeypatch):
        async def fake_fetch(latitude, longitude):
            raise httpx.TimeoutException("timed out")

        monkeypatch.setattr(reverse_geocode_service, "_fetch_nominatim", fake_fetch)

        assert _run(reverse_geocode_service.reverse_geocode(1.0, 2.0)) is None

    def test_returns_none_on_http_error(self, monkeypatch):
        async def fake_fetch(latitude, longitude):
            request = httpx.Request("GET", "https://nominatim.openstreetmap.org/reverse")
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("service unavailable", request=request, response=response)

        monkeypatch.setattr(reverse_geocode_service, "_fetch_nominatim", fake_fetch)

        assert _run(reverse_geocode_service.reverse_geocode(1.0, 2.0)) is None

    def test_returns_none_on_malformed_json(self, monkeypatch):
        async def fake_fetch(latitude, longitude):
            raise ValueError("invalid JSON")

        monkeypatch.setattr(reverse_geocode_service, "_fetch_nominatim", fake_fetch)

        assert _run(reverse_geocode_service.reverse_geocode(1.0, 2.0)) is None

    def test_never_raises(self, monkeypatch):
        """A geocoder outage must not fail the whole image analysis."""

        async def fake_fetch(latitude, longitude):
            raise httpx.RequestError("connection refused")

        monkeypatch.setattr(reverse_geocode_service, "_fetch_nominatim", fake_fetch)

        try:
            result = _run(reverse_geocode_service.reverse_geocode(1.0, 2.0))
        except Exception as e:
            pytest.fail(f"reverse_geocode raised unexpectedly: {e}")
        assert result is None
