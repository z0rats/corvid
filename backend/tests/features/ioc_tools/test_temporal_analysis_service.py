"""Each underlying source (WHOIS/SSL/Wayback/schema.org) is monkeypatched
directly - its own lookup logic is covered by that source's dedicated test
module. These tests focus on temporal_analysis_service's own job: merging,
categorizing, sorting, and tolerating a per-source failure."""

import asyncio
from datetime import UTC, datetime

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    SchemaOrgDate,
    SslInfoResponse,
    TemporalAnalysisRequest,
    WaybackLookupResponse,
    WhoisLookupResponse,
)
from app.features.ioc_tools.domain_finder.service import temporal_analysis_service
from app.features.ioc_tools.domain_finder.service.temporal_analysis_service import (
    perform_temporal_analysis,
)


def _run(coro):
    return asyncio.run(coro)


def _dt(year: int, month: int = 1, day: int = 1) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def _whois(**overrides):
    return WhoisLookupResponse(domain="example.com", rdap_server="rdap.example", **overrides)


def _ssl(**overrides):
    defaults = {
        "domain": "example.com",
        "subject": "CN=example.com",
        "issuer": "CN=Test CA",
        "serial_number": "01",
        "not_before": _dt(2024, 1, 1),
        "not_after": _dt(2025, 1, 1),
        "days_until_expiry": 30,
        "is_expired": False,
        "hostname_matches": True,
    }
    defaults.update(overrides)
    return SslInfoResponse(**defaults)


def _wayback(**overrides):
    return WaybackLookupResponse(domain="example.com", total_snapshots=0, **overrides)


def _patch_all(
    monkeypatch,
    *,
    whois=None,
    whois_exc=None,
    ssl=None,
    ssl_exc=None,
    wayback=None,
    wayback_exc=None,
    schema_org=None,
    schema_org_exc=None,
):
    async def fake_whois(_request):
        if whois_exc:
            raise whois_exc
        return whois or _whois()

    async def fake_ssl(_request):
        if ssl_exc:
            raise ssl_exc
        return ssl or _ssl()

    async def fake_wayback(_request):
        if wayback_exc:
            raise wayback_exc
        return wayback or _wayback()

    async def fake_schema_org(_domain):
        if schema_org_exc:
            raise schema_org_exc
        return schema_org if schema_org is not None else []

    monkeypatch.setattr(temporal_analysis_service, "perform_whois_lookup", fake_whois)
    monkeypatch.setattr(temporal_analysis_service, "perform_ssl_info_lookup", fake_ssl)
    monkeypatch.setattr(temporal_analysis_service, "perform_wayback_lookup", fake_wayback)
    monkeypatch.setattr(temporal_analysis_service, "fetch_schema_org_dates", fake_schema_org)


def test_merges_and_sorts_events_from_every_source(monkeypatch):
    _patch_all(
        monkeypatch,
        whois=_whois(creation_date=_dt(2015), expiration_date=_dt(2030)),
        ssl=_ssl(not_before=_dt(2024), not_after=_dt(2025)),
        wayback=_wayback(first_capture=_dt(2016), last_capture=_dt(2023)),
        schema_org=[SchemaOrgDate(field="dateCreated", value=_dt(2018))],
    )

    result = _run(perform_temporal_analysis(TemporalAnalysisRequest(domain="example.com")))

    assert result.sources_failed == []
    assert [e.date.year for e in result.events] == [2015, 2016, 2018, 2023, 2024, 2025, 2030]


def test_categorizes_server_vs_page_sources(monkeypatch):
    _patch_all(
        monkeypatch,
        whois=_whois(creation_date=_dt(2015)),
        wayback=_wayback(first_capture=_dt(2016)),
    )

    result = _run(perform_temporal_analysis(TemporalAnalysisRequest(domain="example.com")))

    by_source = {e.source: e.category for e in result.events}
    assert by_source["whois"] == "server"
    assert by_source["ssl_certificate"] == "server"
    assert by_source["wayback"] == "page"


def test_a_failed_source_is_recorded_and_excluded_without_failing_the_request(monkeypatch):
    _patch_all(
        monkeypatch,
        ssl_exc=AppHTTPException(
            status_code=502, detail="no listener", error_code="SSL_INFO_CONNECTION_ERROR"
        ),
        whois=_whois(creation_date=_dt(2015)),
    )

    result = _run(perform_temporal_analysis(TemporalAnalysisRequest(domain="example.com")))

    assert result.sources_failed == ["ssl_certificate"]
    assert all(e.source != "ssl_certificate" for e in result.events)
    assert any(e.source == "whois" for e in result.events)


def test_whois_with_no_dates_contributes_no_events(monkeypatch):
    _patch_all(monkeypatch, whois=_whois())

    result = _run(perform_temporal_analysis(TemporalAnalysisRequest(domain="example.com")))

    assert result.sources_failed == []
    assert not any(e.source == "whois" for e in result.events)


def test_an_unexpected_exception_is_also_tolerated(monkeypatch):
    _patch_all(monkeypatch, wayback_exc=RuntimeError("boom"))

    result = _run(perform_temporal_analysis(TemporalAnalysisRequest(domain="example.com")))

    assert result.sources_failed == ["wayback"]


def test_temporal_analysis_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        TemporalAnalysisRequest(domain="example-*")
