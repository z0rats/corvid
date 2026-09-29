"""msp_service against rows captured live from rmsp.nalog.ru on 2026-09-28 (trimmed)."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from app.features.ru_business_check.service.msp_service import (
    MspError,
    fetch_msp_status,
    parse_msp,
)

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "msp_search.json").read_text())
IP_INN = "504110181262"
LE_INN = "5404016083"


def _run(coro):
    return asyncio.run(coro)


class TestParseMsp:
    def test_an_entrepreneur_row(self):
        result = parse_msp(FIXTURE, IP_INN)
        assert result["found"] is True
        assert result["category_code"] == 1
        assert result["category"] == "Микропредприятие"
        assert result["is_active"] is True
        assert result["is_new"] is True  # isnew: 1 in the live row
        assert result["registered_at"] == "10.05.2026"
        assert result["removed_at"] is None

    def test_a_legal_entity_row_is_not_new(self):
        result = parse_msp(FIXTURE, LE_INN)
        assert result["is_new"] is False
        assert result["registered_at"] == "01.08.2016"

    def test_empty_data_is_the_normal_not_listed_answer(self):
        result = parse_msp({"data": [], "rowCount": 0}, "7707083893")
        assert result == {
            "checked": True,
            "found": False,
            "category_code": None,
            "category": None,
            "is_active": None,
            "is_new": None,
            "registered_at": None,
            "removed_at": None,
        }

    def test_a_fuzzy_row_with_another_inn_is_not_a_match(self):
        assert parse_msp(FIXTURE, "7707083893")["found"] is False

    def test_a_struck_off_entity_is_reported_inactive_with_its_removal_date(self):
        row = {
            **FIXTURE["data"][1],
            "is_active": 0,
            "dtregistryout": "01.01.2025 00:00:00",
        }
        result = parse_msp({"data": [row]}, LE_INN)
        assert result["is_active"] is False
        assert result["removed_at"] == "01.01.2025"

    @pytest.mark.parametrize(
        "bad",
        [
            None,
            {},
            {"data": "x"},
            {"data": [{"inn": IP_INN}]},
            {"data": [{**FIXTURE["data"][0], "category": 9}]},
            {"data": [{**FIXTURE["data"][0], "category": "1"}]},
        ],
    )
    def test_drift_raises(self, bad):
        with pytest.raises(MspError, match="схема ответа изменилась"):
            parse_msp(bad, IP_INN)


class TestFetch:
    def test_fetch_returns_result_and_raw(self, patch_httpx_transport):
        def handler(request):
            assert request.url.params["query"] == IP_INN
            assert request.headers["user-agent"].startswith("Corvid-OSINT")
            return httpx.Response(200, json=FIXTURE)

        patch_httpx_transport(handler)
        result, raw = _run(fetch_msp_status(IP_INN, is_individual=True))
        assert result["category"] == "Микропредприятие"
        assert json.loads(raw)["rowCount"] == 2

    def test_http_error_and_non_json_are_clean_errors(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(500, text="x"))
        with pytest.raises(MspError, match="HTTP 500"):
            _run(fetch_msp_status(IP_INN, is_individual=True))

    def test_non_json_page(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(200, text="<html>"))
        with pytest.raises(MspError, match="не-JSON"):
            _run(fetch_msp_status(IP_INN, is_individual=True))

    def test_empty_inn_makes_no_request(self, patch_httpx_transport):
        def fail(request):
            raise AssertionError("no request expected")

        patch_httpx_transport(fail)
        result, raw = _run(fetch_msp_status("", is_individual=False))
        assert result["checked"] is False and raw == ""
