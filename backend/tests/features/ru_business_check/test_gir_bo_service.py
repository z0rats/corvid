"""gir_bo_service against JSON captured live from bo.nalog.gov.ru on 2026-09-28
(АО «ДИКСИ ЮГ», ИНН 5036045205; fixtures trimmed to the fields the parser reads)."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.features.ru_business_check.service.gir_bo_service import (
    GirBoBlocked,
    GirBoError,
    fetch_gir_bo_financials,
    parse_year,
    pick_organization,
    pick_periods,
)

FIXTURES = Path(__file__).parent / "fixtures"
INN = "5036045205"
SEARCH = json.loads((FIXTURES / "gir_bo_search.json").read_text())
BFO = json.loads((FIXTURES / "gir_bo_bfo.json").read_text())
DETAILS_2025 = json.loads((FIXTURES / "gir_bo_details_2025.json").read_text())


def _run(coro):
    return asyncio.run(coro)


class TestPickOrganization:
    def test_matches_the_html_wrapped_inn(self):
        # The live search highlights the match: "inn": "<strong>5036045205</strong>".
        assert SEARCH["content"][0]["inn"] == f"<strong>{INN}</strong>"
        assert pick_organization(SEARCH, INN)["id"] == 4087926

    def test_a_fuzzy_hit_with_another_inn_is_not_a_match(self):
        assert pick_organization(SEARCH, "7707083893") is None

    def test_empty_content_is_no_match_not_drift(self):
        assert pick_organization({"content": []}, INN) is None

    @pytest.mark.parametrize("bad", [None, {}, {"content": "x"}, {"content": [{"id": 1}]}])
    def test_drift_raises(self, bad):
        with pytest.raises(GirBoError, match="схема ответа изменилась"):
            pick_organization(bad, INN)


class TestPickPeriods:
    def test_newest_three_periods_newest_first(self):
        assert [p["period"] for p in pick_periods(BFO)] == ["2025", "2024", "2023"]

    def test_a_refiled_period_keeps_the_most_recent_filing(self):
        bfo = [
            {"id": 1, "period": "2024", "actualBfoDate": "2025-03-01"},
            {"id": 2, "period": "2024", "actualBfoDate": "2025-06-01"},
        ]
        assert [p["id"] for p in pick_periods(bfo)] == [2]

    @pytest.mark.parametrize("bad", [None, {}, [{"id": 1}], [{"id": 1, "period": "abc"}]])
    def test_drift_raises(self, bad):
        with pytest.raises(GirBoError, match="схема ответа изменилась"):
            pick_periods(bad)


class TestParseYear:
    def test_detail_lines_from_the_live_form(self):
        period = next(p for p in BFO if p["period"] == "2025")
        year = parse_year(period, DETAILS_2025)
        assert year["year"] == 2025
        assert year["detail_loaded"] is True
        assert year["revenue"] == 396350822.0  # line 2110 == the list's gainSum
        assert year["net_profit"] == 4137844.0
        assert year["assets"] == 242547340.0
        assert year["equity"] == 79368565.0
        assert year["current_assets"] == 98303815.0
        assert year["current_liabilities"] == 58328857.0
        assert year["cash"] == 6057184.0

    def test_without_a_detail_form_only_list_level_revenue_and_assets_are_filled(self):
        period = next(p for p in BFO if p["period"] == "2024")
        year = parse_year(period, None)
        assert year["revenue"] == 343973748.0
        assert year["assets"] == 219012814.0
        assert year["equity"] is None
        assert year["detail_loaded"] is False

    def test_null_lines_are_data_not_drift(self):
        detail = [{"balance": {"current1600": None}, "financialResult": {"current2110": None}}]
        year = parse_year({"id": 1, "period": "2025", "gainSum": 5, "actives": 9}, detail)
        assert year["revenue"] == 5 and year["assets"] == 9  # list-level values survive

    @pytest.mark.parametrize("bad", [{}, [{"balance": {}}], [{"financialResult": {}}], ["x"]])
    def test_form_without_its_sections_is_drift(self, bad):
        with pytest.raises(GirBoError, match="схема ответа изменилась"):
            parse_year({"id": 1, "period": "2025"}, bad)


def _router(search=SEARCH, bfo=BFO, details=DETAILS_2025, detail_status=200):
    def handler(request):
        path = request.url.path
        # The library-default UA is refused by the site; ours must identify the tool instead.
        assert request.headers["user-agent"].startswith("Corvid-OSINT")
        if path.endswith("/organizations/search"):
            return httpx.Response(200, json=search)
        if path.endswith("/bfo/"):
            return httpx.Response(200, json=bfo)
        if path.endswith("/details"):
            if detail_status != 200:
                return httpx.Response(detail_status, text="x")
            return httpx.Response(200, json=details)
        raise AssertionError(path)

    return handler


class TestFetch:
    def test_full_flow_returns_years_and_raw(self, patch_httpx_transport):
        patch_httpx_transport(_router())
        result, raw = _run(fetch_gir_bo_financials(INN, is_individual=False))
        assert result["checked"] and result["found"] and result["has_reports"]
        assert [y["year"] for y in result["years"]] == [2025, 2024, 2023]
        assert result["org_name"] == 'АО "ДИКСИ ЮГ"'
        assert json.loads(raw)["search"]["content"][0]["id"] == 4087926

    def test_organization_absent_is_a_checked_empty_result(self, patch_httpx_transport):
        patch_httpx_transport(_router(search={"content": []}))
        result, _ = _run(fetch_gir_bo_financials("7707083893", is_individual=False))
        assert result["checked"] is True
        assert result["found"] is False
        assert result["years"] == []
        assert "банк" in result["note"]

    def test_organization_without_published_periods_is_empty_with_a_note(
        self, patch_httpx_transport
    ):
        patch_httpx_transport(_router(bfo=[]))
        result, _ = _run(fetch_gir_bo_financials(INN, is_individual=False))
        assert result["found"] is True
        assert result["has_reports"] is False
        assert "отчётности нет" in result["note"]

    def test_individual_entrepreneur_makes_no_request(self, patch_httpx_transport):
        def fail(request):
            raise AssertionError("no request expected")

        patch_httpx_transport(fail)
        result, raw = _run(fetch_gir_bo_financials("771234567890", is_individual=True))
        assert result["checked"] is True and result["found"] is False
        assert raw == ""

    def test_every_detail_form_failing_is_an_error_not_a_pass(self, patch_httpx_transport):
        patch_httpx_transport(_router(detail_status=500))
        with pytest.raises(GirBoError, match="детальные формы"):
            _run(fetch_gir_bo_financials(INN, is_individual=False))

    def test_some_detail_forms_failing_keeps_the_rest_and_says_so(self, patch_httpx_transport):
        good = _router()

        def handler(request):
            if request.url.path.endswith("/details") and "21912564" in str(request.url):
                return httpx.Response(500, text="x")
            return good(request)

        patch_httpx_transport(handler)
        # The 2023 period (id 21912564) fails; 2025/2024 load.
        result, _ = _run(fetch_gir_bo_financials(INN, is_individual=False))
        by_year = {y["year"]: y for y in result["years"]}
        assert by_year[2025]["detail_loaded"] and not by_year[2023]["detail_loaded"]
        assert "2023" in result["note"]

    def test_an_antibot_status_is_blocked_not_a_raw_http_error(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(403, text="x"))
        with pytest.raises(GirBoBlocked):
            _run(fetch_gir_bo_financials(INN, is_individual=False))

    def test_a_non_json_page_is_a_clean_error(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(200, text="<html>"))
        with pytest.raises(GirBoError, match="не-JSON"):
            _run(fetch_gir_bo_financials(INN, is_individual=False))

    def test_network_errors_become_gir_bo_errors(self, patch_httpx_transport):
        def boom(request):
            raise httpx.ConnectTimeout("t")

        patch_httpx_transport(boom)
        with pytest.raises(GirBoError, match="недоступен"):
            _run(fetch_gir_bo_financials(INN, is_individual=False))
