import asyncio

import pytest

from app.features.image_tools.service import chronoverify_service


def _run(coro):
    return asyncio.run(coro)


class _FakeApikey:
    def __init__(self, key: str, is_active: bool = True):
        self.key = key
        self.is_active = is_active


RAW_VERDICT = {
    "verdict": "manipulation_indicated",
    "confidence": 60,
    "summary": "Multiple signals are consistent with possible editing",
    "capture_time": {"value": "2026-03-14T09:21:30", "source": "exif"},
    "capture_device": {"make": "Canon", "model": "EOS R6"},
    "capture_location": {
        "present": True,
        "place": "near Sedona, Arizona",
        "city": None,
        "region": "Arizona",
        "country": "US",
        "lat": 34.8697,
        "lon": -111.761,
    },
    "c2pa": {"present": False, "validated": False},
    "signals": [
        {
            "name": "ela_localized_anomaly",
            "layer": "pixel",
            "direction": "anomalous",
            "detail": "weak signal",
        },
    ],
    "integrity": {"sha256": "abc123"},
}


class TestGetChronoverifyKey:
    def test_returns_none_when_no_row_exists(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            assert name == "chronoverify"
            return None

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        assert _run(chronoverify_service._get_chronoverify_key(db=None)) is None

    def test_returns_none_when_inactive(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return _FakeApikey("key", is_active=False)

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        assert _run(chronoverify_service._get_chronoverify_key(db=None)) is None

    def test_returns_key_when_active(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return _FakeApikey("cv_live_x", is_active=True)

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        assert _run(chronoverify_service._get_chronoverify_key(db=None)) == "cv_live_x"


class TestCheckImageProvenance:
    def test_maps_full_response(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return None

        async def _fake_fetch(filename, data, api_key):
            assert api_key is None
            return RAW_VERDICT

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        monkeypatch.setattr(chronoverify_service, "fetch_chronoverify_verdict", _fake_fetch)

        result = _run(chronoverify_service.check_image_provenance("photo.jpg", b"data", db=None))

        assert result.verdict == "manipulation_indicated"
        assert result.confidence == 60
        assert result.capture_time == "2026-03-14T09:21:30"
        assert result.capture_device.make == "Canon"
        assert result.capture_device.model == "EOS R6"
        assert result.location.present is True
        assert result.location.latitude == 34.8697
        assert result.c2pa.present is False
        assert len(result.signals) == 1
        assert result.signals[0].name == "ela_localized_anomaly"
        assert result.sha256 == "abc123"

    def test_uses_configured_key_when_present(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return _FakeApikey("cv_live_x", is_active=True)

        captured = {}

        async def _fake_fetch(filename, data, api_key):
            captured["api_key"] = api_key
            return RAW_VERDICT

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        monkeypatch.setattr(chronoverify_service, "fetch_chronoverify_verdict", _fake_fetch)

        _run(chronoverify_service.check_image_provenance("photo.jpg", b"data", db=None))

        assert captured["api_key"] == "cv_live_x"

    def test_handles_missing_optional_fields(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return None

        async def _fake_fetch(filename, data, api_key):
            return {
                "verdict": "inconclusive",
                "confidence": 30,
                "summary": "No evidence survives in the file",
            }

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        monkeypatch.setattr(chronoverify_service, "fetch_chronoverify_verdict", _fake_fetch)

        result = _run(chronoverify_service.check_image_provenance("photo.jpg", b"data", db=None))

        assert result.verdict == "inconclusive"
        assert result.capture_time is None
        assert result.capture_device is None
        assert result.location is None
        assert result.c2pa is None
        assert result.signals == []
        assert result.sha256 is None

    def test_skips_malformed_signal_entries(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return None

        async def _fake_fetch(filename, data, api_key):
            return {
                "verdict": "consistent",
                "confidence": 90,
                "summary": "ok",
                "signals": [{"layer": "pixel", "direction": "neutral", "detail": "missing name"}],
            }

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        monkeypatch.setattr(chronoverify_service, "fetch_chronoverify_verdict", _fake_fetch)

        result = _run(chronoverify_service.check_image_provenance("photo.jpg", b"data", db=None))

        assert result.signals == []

    def test_propagates_value_error_from_api(self, monkeypatch):
        async def _fake_get_apikey(db, name):
            return None

        async def _fake_fetch(filename, data, api_key):
            raise ValueError("ChronoVerify rate limit reached")

        monkeypatch.setattr(chronoverify_service, "get_apikey", _fake_get_apikey)
        monkeypatch.setattr(chronoverify_service, "fetch_chronoverify_verdict", _fake_fetch)

        with pytest.raises(ValueError):
            _run(chronoverify_service.check_image_provenance("photo.jpg", b"data", db=None))
