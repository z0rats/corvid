"""safe_get is monkeypatched directly (rather than exercised through real DNS
resolution/SSRF checks, already covered by test_ssrf_guard.py) so these tests
focus on schema_org_service's own logic: JSON-LD extraction shapes and
best-effort failure handling."""

import asyncio

import httpx

from app.core.security.ssrf_guard import SSRFValidationError
from app.features.ioc_tools.domain_finder.service import schema_org_service
from app.features.ioc_tools.domain_finder.service.schema_org_service import (
    _extract_dates,
    fetch_schema_org_dates,
)


def _run(coro):
    return asyncio.run(coro)


def _html_response(html: str, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/")
    return httpx.Response(status_code, content=html.encode(), request=request)


def _patch_safe_get(monkeypatch, result=None, exc=None):
    async def fake_safe_get(client, url, **kwargs):
        if exc:
            raise exc
        return result

    monkeypatch.setattr(schema_org_service, "safe_get", fake_safe_get)


def test_extracts_dates_from_a_single_json_ld_object():
    html = """
    <script type="application/ld+json">
    {"@type": "WebPage", "dateCreated": "2020-01-01T00:00:00Z",
     "dateModified": "2021-06-15T00:00:00Z"}
    </script>
    """
    dates = _extract_dates(html)

    fields = {d.field: d.value.year for d in dates}
    assert fields == {"dateCreated": 2020, "dateModified": 2021}


def test_extracts_dates_from_a_graph_wrapped_list():
    html = """
    <script type="application/ld+json">
    {"@graph": [{"@type": "Article", "datePublished": "2022-03-10T00:00:00Z"}]}
    </script>
    """
    dates = _extract_dates(html)

    assert len(dates) == 1
    assert dates[0].field == "datePublished"
    assert dates[0].value.year == 2022


def test_ignores_malformed_json_ld():
    html = '<script type="application/ld+json">{not valid json</script>'
    assert _extract_dates(html) == []


def test_ignores_json_ld_without_recognized_date_fields():
    html = '<script type="application/ld+json">{"@type": "WebPage", "name": "Example"}</script>'
    assert _extract_dates(html) == []


def test_fetch_returns_empty_list_on_ssrf_rejection(monkeypatch):
    _patch_safe_get(monkeypatch, exc=SSRFValidationError("resolves to a private address"))
    assert _run(fetch_schema_org_dates("internal.example")) == []


def test_fetch_returns_empty_list_on_connection_error(monkeypatch):
    _patch_safe_get(monkeypatch, exc=httpx.ConnectError("refused"))
    assert _run(fetch_schema_org_dates("example.com")) == []


def test_fetch_returns_empty_list_on_non_2xx_status(monkeypatch):
    _patch_safe_get(monkeypatch, result=_html_response("<html></html>", status_code=404))
    assert _run(fetch_schema_org_dates("example.com")) == []


def test_fetch_parses_dates_from_a_successful_response(monkeypatch):
    html = (
        '<script type="application/ld+json">'
        '{"@type": "WebPage", "dateCreated": "2019-05-01T00:00:00Z"}'
        "</script>"
    )
    _patch_safe_get(monkeypatch, result=_html_response(html))

    dates = _run(fetch_schema_org_dates("example.com"))

    assert len(dates) == 1
    assert dates[0].field == "dateCreated"
