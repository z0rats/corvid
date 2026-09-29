"""Uses httpx.MockTransport (stdlib to httpx, no extra dependency) rather than
mocking away httpx.AsyncClient's behavior, so the real HTML-table parsing in
fetch_rapiddns_records runs against a canned response. The fixture HTML below
mirrors RapidDNS's actual markup: an `<a>`-wrapped address cell, multi-line
whitespace inside cells, and the row/table structure it serves."""

import asyncio

import httpx

from app.features.ioc_tools.domain_finder.service.rapiddns_api_service import (
    fetch_rapiddns_records,
)


def _run(coro):
    return asyncio.run(coro)


def _table_html(rows_html: str) -> str:
    return f"""
    <html><body>
    <table id="table">
        <thead>
            <tr><th>#</th><th>Domain</th><th>Address</th><th>Type</th><th>Date</th></tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    </body></html>
    """


ROW_TEMPLATE = """
<tr>
    <th scope="row ">{index}</th>
    <td>{hostname}</td>
    <td><a href="/sameip/{address}#result" target="_blank" title="same ip">
            {address}
        </a>
    </td>
    <td>{record_type}</td>
    <td>2026-08-23</td>
</tr>
"""


def test_returns_parsed_records_on_success(patch_httpx_transport):
    html = _table_html(
        ROW_TEMPLATE.format(
            index=1, hostname="www.example.com", address="93.184.216.34", record_type="A"
        )
        + ROW_TEMPLATE.format(
            index=2, hostname="example.com", address="93.184.216.34", record_type="A"
        )
    )

    def handler(request):
        assert request.url.params["full"] == "1"
        assert "/subdomain/example.com" in str(request.url)
        return httpx.Response(200, text=html)

    patch_httpx_transport(handler)

    result = _run(fetch_rapiddns_records("example.com"))

    assert result == [
        ("www.example.com", "A", "93.184.216.34"),
        ("example.com", "A", "93.184.216.34"),
    ]


def test_returns_empty_list_for_empty_tbody(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, text=_table_html("")))

    assert _run(fetch_rapiddns_records("doesnotexist.example")) == []


def test_returns_empty_list_for_empty_response_body(patch_httpx_transport):
    patch_httpx_transport(lambda request: httpx.Response(200, content=b""))

    assert _run(fetch_rapiddns_records("example.com")) == []


def test_skips_rows_with_too_few_columns(patch_httpx_transport):
    malformed_row = "<tr><td>onlyonecolumn</td></tr>"
    patch_httpx_transport(lambda request: httpx.Response(200, text=_table_html(malformed_row)))

    assert _run(fetch_rapiddns_records("example.com")) == []
