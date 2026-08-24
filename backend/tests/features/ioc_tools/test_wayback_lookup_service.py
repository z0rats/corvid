import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import WaybackLookupRequest
from app.features.ioc_tools.domain_finder.service import wayback_lookup_service
from app.features.ioc_tools.domain_finder.service.wayback_lookup_service import (
    _parse_cdx_timestamp,
    perform_wayback_lookup,
)

CDX_SAMPLE = [
    {
        "timestamp": "20260730120433",
        "original": "http://example.com/",
        "mimetype": "text/html",
        "statuscode": "200",
    },
    {
        "timestamp": "20200101000000",
        "original": "http://example.com/",
        "mimetype": "text/html",
        "statuscode": "200",
    },
]


def test_parse_cdx_timestamp_parses_valid_timestamp():
    parsed = _parse_cdx_timestamp("20260730120433")

    assert parsed is not None
    assert parsed.year == 2026 and parsed.month == 7 and parsed.day == 30


def test_parse_cdx_timestamp_returns_none_for_invalid():
    assert _parse_cdx_timestamp("not-a-timestamp") is None


def test_perform_wayback_lookup_sorts_oldest_first_and_derives_capture_range(monkeypatch):
    async def fake_fetch(domain, path=None):
        return CDX_SAMPLE

    monkeypatch.setattr(wayback_lookup_service, "fetch_wayback_snapshots", fake_fetch)

    result = asyncio.run(perform_wayback_lookup(WaybackLookupRequest(domain="example.com")))

    assert result.domain == "example.com"
    assert result.total_snapshots == 2
    assert [s.timestamp for s in result.snapshots] == ["20200101000000", "20260730120433"]
    assert result.first_capture.year == 2020
    assert result.last_capture.year == 2026


def test_perform_wayback_lookup_builds_snapshot_url_from_timestamp_and_original(monkeypatch):
    async def fake_fetch(domain, path=None):
        return [CDX_SAMPLE[0]]

    monkeypatch.setattr(wayback_lookup_service, "fetch_wayback_snapshots", fake_fetch)

    result = asyncio.run(perform_wayback_lookup(WaybackLookupRequest(domain="example.com")))

    assert result.snapshots[0].snapshot_url == (
        "https://web.archive.org/web/20260730120433/http://example.com/"
    )


def test_perform_wayback_lookup_handles_empty_response(monkeypatch):
    async def fake_fetch(domain, path=None):
        return []

    monkeypatch.setattr(wayback_lookup_service, "fetch_wayback_snapshots", fake_fetch)

    result = asyncio.run(
        perform_wayback_lookup(WaybackLookupRequest(domain="doesnotexist.example"))
    )

    assert result.snapshots == []
    assert result.total_snapshots == 0
    assert result.first_capture is None
    assert result.last_capture is None


def test_perform_wayback_lookup_propagates_fetch_errors(monkeypatch):
    async def fake_fetch(domain, path=None):
        raise AppHTTPException(status_code=504, detail="timeout", error_code="WAYBACK_TIMEOUT")

    monkeypatch.setattr(wayback_lookup_service, "fetch_wayback_snapshots", fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(perform_wayback_lookup(WaybackLookupRequest(domain="example.com")))

    assert exc_info.value.status_code == 504


def test_wayback_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        WaybackLookupRequest(domain="example-*")


def test_wayback_request_normalizes_protocol_and_path():
    req = WaybackLookupRequest(domain="HTTPS://Example.COM/path", path="login")

    assert req.domain == "example.com"
    assert req.path == "/login"


def test_wayback_request_defaults_path_to_none():
    req = WaybackLookupRequest(domain="example.com")

    assert req.path is None
