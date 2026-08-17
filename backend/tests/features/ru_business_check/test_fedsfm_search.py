"""fedsfm_service._search / check_terrorist_list network behavior, using
httpx.MockTransport (same pattern as test_fedresurs_search.py) so status-code handling and
response.json() parsing run for real against a canned response.

The bare-403-without-a-User-Agent behavior is a regression test for the real WAF behavior
observed live during development: fedsfm.ru's own WAF rejects any request without a
browser-shaped User-Agent header - this must surface as a clean, user-facing FedsfmError,
not a raw httpx exception.
"""

import asyncio

import httpx
import pytest

from app.features.ru_business_check.service.fedsfm_service import (
    FedsfmError,
    _parse_matches,
    check_terrorist_list,
)


def _run(coro):
    return asyncio.run(coro)


def _patch_transport(monkeypatch, handler):
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


class TestParseMatches:
    def test_extracts_id_name_type_status_from_each_row(self):
        data = {
            "data": [
                {
                    "Id": "8bb9bed0-e8b6-431c-8ff8-12d609d3e8a4",
                    "TerroristTypeName": "Национальный",
                    "FullName": "10198. КОСЯКОВ ДМИТРИЙ ЕВГЕНЬЕВИЧ, 06.06.1989 г.р.",
                    "StatusName": "Физическое лицо",
                }
            ]
        }
        matches = _parse_matches(data)
        assert matches == [
            {
                "id": "8bb9bed0-e8b6-431c-8ff8-12d609d3e8a4",
                "full_name": "10198. КОСЯКОВ ДМИТРИЙ ЕВГЕНЬЕВИЧ, 06.06.1989 г.р.",
                "terrorist_type": "Национальный",
                "status": "Физическое лицо",
            }
        ]

    def test_rows_without_a_full_name_are_dropped(self):
        data = {"data": [{"Id": "x", "TerroristTypeName": "Национальный", "StatusName": "..."}]}
        assert _parse_matches(data) == []

    def test_missing_data_key_is_an_empty_list(self):
        assert _parse_matches({}) == []


class TestBlockedDetection:
    def test_a_403_with_no_user_agent_raises_a_clean_error(self, monkeypatch):
        _patch_transport(monkeypatch, lambda request: httpx.Response(403, text="Forbidden"))

        with pytest.raises(FedsfmError, match="HTTP 403"):
            _run(check_terrorist_list("Иванов Иван Иванович"))

    def test_an_unrelated_server_error_raises_a_clean_error_not_the_raw_httpx_exception(
        self, monkeypatch
    ):
        _patch_transport(monkeypatch, lambda request: httpx.Response(500, text="internal error"))

        with pytest.raises(FedsfmError, match="HTTP 500"):
            _run(check_terrorist_list("Иванов Иван Иванович"))

    def test_a_non_json_body_raises_a_clean_error(self, monkeypatch):
        _patch_transport(
            monkeypatch, lambda request: httpx.Response(200, text="<html>block</html>")
        )

        with pytest.raises(FedsfmError, match="не JSON"):
            _run(check_terrorist_list("Иванов Иван Иванович"))

    def test_is_error_true_raises_a_clean_error(self, monkeypatch):
        _patch_transport(
            monkeypatch,
            lambda request: httpx.Response(
                200, json={"IsError": True, "recordsTotal": 0, "recordsFiltered": 0, "data": []}
            ),
        )

        with pytest.raises(FedsfmError):
            _run(check_terrorist_list("Иванов Иван Иванович"))


class TestSuccessPath:
    def test_sends_the_search_text_and_a_browser_user_agent(self, monkeypatch):
        captured = {}

        def handler(request):
            captured["body"] = request.content
            captured["user_agent"] = request.headers.get("user-agent")
            return httpx.Response(
                200, json={"IsError": False, "recordsTotal": 0, "recordsFiltered": 0, "data": []}
            )

        _patch_transport(monkeypatch, handler)

        _run(check_terrorist_list("Иванов Иван Иванович"))

        assert "Иванов".encode() in captured["body"]
        assert captured["user_agent"]

    def test_returns_clean_result_and_raw_payload_when_matched(self, monkeypatch):
        payload = {
            "IsError": False,
            "recordsTotal": 1,
            "recordsFiltered": 1,
            "data": [
                {
                    "Id": "abc",
                    "TerroristTypeName": "Национальный",
                    "FullName": "1. ИВАНОВ ИВАН ИВАНОВИЧ, 01.01.1980 г.р.",
                    "StatusName": "Физическое лицо",
                }
            ],
        }
        _patch_transport(monkeypatch, lambda request: httpx.Response(200, json=payload))

        result, raw = _run(check_terrorist_list("Иванов Иван Иванович"))

        assert result == {
            "checked": True,
            "matched": True,
            "requires_manual_review": True,
            "matches": [
                {
                    "id": "abc",
                    "full_name": "1. ИВАНОВ ИВАН ИВАНОВИЧ, 01.01.1980 г.р.",
                    "terrorist_type": "Национальный",
                    "status": "Физическое лицо",
                }
            ],
        }
        assert "ИВАНОВ" in raw

    def test_no_matching_row_is_a_clean_not_matched_result_not_an_error(self, monkeypatch):
        payload = {"IsError": False, "recordsTotal": 0, "recordsFiltered": 0, "data": []}
        _patch_transport(monkeypatch, lambda request: httpx.Response(200, json=payload))

        result, _ = _run(check_terrorist_list("Совершенно Несуществующее Имя"))

        assert result == {
            "checked": True,
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }

    def test_empty_name_short_circuits_without_a_network_call(self, monkeypatch):
        def fail_handler(request):
            raise AssertionError("should not have made a request")

        _patch_transport(monkeypatch, fail_handler)

        result, raw = _run(check_terrorist_list(""))

        assert result["checked"] is False
        assert raw == ""
