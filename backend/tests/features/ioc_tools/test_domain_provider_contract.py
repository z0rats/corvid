"""Structural gate: every third-party `Provider` in domain_finder turns a drifted response into
`<CODE>_SCHEMA_DRIFT` (HTTP 502) - never into an empty result - and still returns `[]` for a
legitimately empty one.

If you add a `Provider`, add it to `DRIFT_CASES` (drifted payloads, and the legitimately empty
answer if the source has one) or to `EXEMPT` with a reason - `test_every_provider_is_covered`
fails until you do, so a new scraper decides up front what schema drift looks like for it."""

import asyncio
import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.core.external_sources.contract import SourceDriftError
from app.features.ioc_tools.domain_finder import service as service_package
from app.features.ioc_tools.domain_finder.service import rdap_api_service
from app.features.ioc_tools.domain_finder.service.crtsh_api_service import fetch_crtsh_certificates
from app.features.ioc_tools.domain_finder.service.hackertarget_api_service import (
    fetch_hackertarget_hosts,
)
from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_errors
from app.features.ioc_tools.domain_finder.service.rapiddns_api_service import (
    fetch_rapiddns_records,
)
from app.features.ioc_tools.domain_finder.service.rdap_api_service import fetch_rdap_domain_data
from app.features.ioc_tools.domain_finder.service.urlscan_api_service import (
    fetch_domain_scan_results,
)
from app.features.ioc_tools.domain_finder.service.wayback_api_service import (
    fetch_wayback_snapshots,
)

DOMAIN = "example.com"
CDX_HEADER = ["urlkey", "timestamp", "original", "mimetype", "statuscode", "digest", "length"]


def _html_table(rows: str = "") -> str:
    return f"<html><body><table id='table'><tbody>{rows}</tbody></table></body></html>"


@dataclass(frozen=True)
class Case:
    fetch: Any  # async callable taking the domain
    drifted: list[dict[str, Any]]  # httpx.Response kwargs, each a payload that must be drift
    empty: list[dict[str, Any]] = field(default_factory=list)  # legitimately empty answers
    empty_result: Any = field(default_factory=list)


DRIFT_CASES = {
    "CRTSH": Case(
        fetch=fetch_crtsh_certificates,
        drifted=[
            {"json": {"error": "overloaded"}},
            {"json": ["not", "objects"]},
            {"json": [{"id": 1}]},  # no name_value
        ],
        empty=[{"json": []}, {"content": b""}],
    ),
    "WAYBACK": Case(
        fetch=lambda d: fetch_wayback_snapshots(d),
        drifted=[
            {"json": {"error": "x"}},
            {"json": [["a", "b"], ["1", "2"]]},  # header without timestamp/original
            {"json": [CDX_HEADER, ["only", "two"]]},  # row narrower than the header
        ],
        empty=[{"json": []}, {"json": [CDX_HEADER]}, {"content": b""}],
    ),
    "HACKERTARGET": Case(
        fetch=fetch_hackertarget_hosts,
        drifted=[
            {"text": "error something new we have never seen"},
            {"text": "Please complete the captcha to continue"},
        ],
        empty=[{"text": "error invalid host"}, {"content": b""}],
    ),
    "RAPIDDNS": Case(
        fetch=fetch_rapiddns_records,
        drifted=[
            {"text": "<html><body>Just a moment...</body></html>"},
            {"text": _html_table("<tr><td>1</td><td>host</td><td>1.1.1.1</td></tr>")},
        ],
        empty=[{"text": _html_table()}, {"content": b""}],
    ),
    "URLSCAN": Case(
        fetch=fetch_domain_scan_results,
        drifted=[
            {"json": {"message": "rate limited"}},
            {"json": {"results": "none"}},
            {"json": {"results": [{"unrelated": 1}]}},
        ],
        empty=[{"json": {"results": []}}],
    ),
    "RDAP": Case(
        fetch=fetch_rdap_domain_data,
        drifted=[{"json": {"message": "x"}}, {"json": ["not", "an", "object"]}],
        # no empty answer: an unknown domain is RDAP_NOT_FOUND (404), covered elsewhere
    ),
}

EXEMPT = {
    "DNSDUMPSTER": "keyed, see 04-keyed-canaries",
}


def _providers() -> dict[str, Provider]:
    found = {}
    for module_info in pkgutil.iter_modules(service_package.__path__):
        module = importlib.import_module(f"{service_package.__name__}.{module_info.name}")
        for value in vars(module).values():
            if isinstance(value, Provider):
                found[value.code] = value
    return found


def _serve(monkeypatch, patch_httpx_transport, code: str, response_kwargs: dict[str, Any]):
    """Answer the provider's request with a canned 200 response."""
    if code == "RDAP":
        request = httpx.Request("GET", "https://rdap.org/domain/x", headers={"host": "rdap.test"})

        async def fake_safe_get(client, url, **kwargs):
            return httpx.Response(200, request=request, **response_kwargs)

        monkeypatch.setattr(rdap_api_service, "safe_get", fake_safe_get)
    else:
        patch_httpx_transport(lambda request: httpx.Response(200, **response_kwargs))


def _drift_ids():
    return [
        (code, i) for code, case in sorted(DRIFT_CASES.items()) for i in range(len(case.drifted))
    ]


def test_every_provider_is_covered():
    providers = set(_providers())
    covered = set(DRIFT_CASES) | set(EXEMPT)
    assert providers == covered, (
        f"add a drift case (or an EXEMPT reason) for {sorted(providers - covered)}; "
        f"remove stale entries {sorted(covered - providers)}"
    )
    assert not set(DRIFT_CASES) & set(EXEMPT)
    assert all(EXEMPT.values()), "an EXEMPT entry needs a reason"


@pytest.mark.parametrize(("code", "index"), _drift_ids())
def test_drifted_payload_is_schema_drift_not_empty(code, index, monkeypatch, patch_httpx_transport):
    case = DRIFT_CASES[code]
    _serve(monkeypatch, patch_httpx_transport, code, case.drifted[index])

    with pytest.raises(AppHTTPException) as caught:
        asyncio.run(case.fetch(DOMAIN))

    assert caught.value.status_code == 502
    assert caught.value.error_code == f"{code}_SCHEMA_DRIFT"
    assert isinstance(caught.value.__cause__, SourceDriftError)


@pytest.mark.parametrize(
    ("code", "index"),
    [(code, i) for code, case in sorted(DRIFT_CASES.items()) for i in range(len(case.empty))],
)
def test_legitimately_empty_answer_is_an_empty_result(
    code, index, monkeypatch, patch_httpx_transport
):
    case = DRIFT_CASES[code]
    _serve(monkeypatch, patch_httpx_transport, code, case.empty[index])

    assert asyncio.run(case.fetch(DOMAIN)) == case.empty_result


def test_provider_errors_maps_drift_apart_from_an_unparseable_body():
    provider = Provider(name="X", code="X", base_url="https://x.test/")

    async def run(exc):
        async with provider_errors(provider, "subject"):
            raise exc

    with pytest.raises(AppHTTPException) as drift:
        asyncio.run(run(SourceDriftError("changed")))
    with pytest.raises(AppHTTPException) as invalid:
        asyncio.run(run(ValueError("<html> is not JSON")))

    assert drift.value.error_code == "X_SCHEMA_DRIFT"
    assert invalid.value.error_code == "X_INVALID_RESPONSE"
