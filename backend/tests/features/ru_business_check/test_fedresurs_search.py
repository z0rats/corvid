"""fedresurs_service._search / fetch_fedresurs_status network behavior, using
httpx.MockTransport (same pattern as test_arbitration_search.py) so status-code handling
and response.json() parsing run for real against a canned response.

The 451/403 block detection is a regression test for the real anti-bot behavior observed
live during development: fedresurs.ru's Qrator layer returned HTTP 451 for an overly
broad test query - this must surface as a clean, user-facing FedresursBlocked, not a raw
httpx exception.
"""

import asyncio

import httpx
import pytest

from app.features.ru_business_check.service.fedresurs_service import (
    FedresursBlocked,
    FedresursError,
    fetch_fedresurs_status,
)


def _run(coro):
    return asyncio.run(coro)


def _patch_transport(monkeypatch, handler):
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


class TestBlockedDetection:
    def test_a_451_raises_a_clean_blocked_error(self, monkeypatch):
        _patch_transport(monkeypatch, lambda request: httpx.Response(451, text="restricted"))

        with pytest.raises(FedresursBlocked, match="ограничил доступ"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_a_403_is_also_treated_as_blocked_not_a_raw_http_error(self, monkeypatch):
        _patch_transport(monkeypatch, lambda request: httpx.Response(403, text="Forbidden"))

        with pytest.raises(FedresursBlocked):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))

    def test_an_unrelated_server_error_raises_a_clean_error_not_the_raw_httpx_exception(
        self, monkeypatch
    ):
        _patch_transport(monkeypatch, lambda request: httpx.Response(500, text="internal error"))

        with pytest.raises(FedresursError, match="HTTP 500"):
            _run(fetch_fedresurs_status("7707083893", is_individual=False))


class TestSuccessPath:
    def test_returns_clean_result_and_raw_payload_when_status_is_not_bankrupt(self, monkeypatch):
        payload = {
            "pageData": [
                {
                    "guid": "9348548a-30a3-4344-8cf0-fb1f45c54dfb",
                    "inn": "7707083893",
                    "name": "ПАО СБЕРБАНК",
                    "status": "Действующее",
                }
            ],
            "found": 1,
        }
        _patch_transport(monkeypatch, lambda request: httpx.Response(200, json=payload))

        result, raw = _run(fetch_fedresurs_status("7707083893", is_individual=False))

        assert result == {
            "checked": True,
            "found": True,
            "status_text": "Действующее",
            "is_active_bankruptcy": False,
            "profile_url": "https://fedresurs.ru/company/9348548a-30a3-4344-8cf0-fb1f45c54dfb",
        }
        assert "СБЕРБАНК" in raw

    def test_returns_active_bankruptcy_flag_when_status_indicates_it(self, monkeypatch):
        payload = {
            "pageData": [
                {
                    "guid": "c3bb33b5-0c41-4ddb-9469-a5fb854c531c",
                    "inn": "7731103741",
                    "status": (
                        "Юридическое лицо признано несостоятельным (банкротом) "
                        "и в отношении него открыто конкурсное производство"
                    ),
                }
            ],
            "found": 1,
        }
        _patch_transport(monkeypatch, lambda request: httpx.Response(200, json=payload))

        result, _ = _run(fetch_fedresurs_status("7731103741", is_individual=False))

        assert result["is_active_bankruptcy"] is True
        assert result["found"] is True

    def test_no_matching_row_is_a_clean_not_found_result_not_an_error(self, monkeypatch):
        payload = {"pageData": [], "found": 0}
        _patch_transport(monkeypatch, lambda request: httpx.Response(200, json=payload))

        result, _ = _run(fetch_fedresurs_status("7707083893", is_individual=False))

        assert result == {
            "checked": True,
            "found": False,
            "status_text": None,
            "is_active_bankruptcy": False,
            "profile_url": None,
        }

    def test_uses_the_persons_endpoint_for_individuals(self, monkeypatch):
        requested_paths = []

        def handler(request):
            requested_paths.append(request.url.path)
            return httpx.Response(200, json={"pageData": [], "found": 0})

        _patch_transport(monkeypatch, handler)

        _run(fetch_fedresurs_status("771234567890", is_individual=True))

        assert requested_paths == ["/backend/persons"]

    def test_empty_inn_short_circuits_without_a_network_call(self, monkeypatch):
        def fail_handler(request):
            raise AssertionError("should not have made a request")

        _patch_transport(monkeypatch, fail_handler)

        result, raw = _run(fetch_fedresurs_status("", is_individual=False))

        assert result["checked"] is False
        assert raw == ""
