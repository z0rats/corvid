"""arbitration_service._search / fetch_arbitration_cases network behavior, using
httpx.MockTransport (stdlib to httpx, no extra dependency - same pattern as
tests/features/ioc_tools/test_crtsh_api_service.py) so status-code handling and
response.json() parsing run for real against a canned response.

The DDoS-Guard block detection is a regression test: a real live capture against
kad.arbitr.ru returned HTTP 451 with a DDoS-Guard-branded HTML page (a rate-limit block,
confirmed live while debugging a user-reported scan failure) - an earlier version of
_search let httpx's raw HTTPStatusError propagate for this, leaking a technical message
to the end user instead of a clean one.
"""

import asyncio

import httpx
import pytest

from app.features.ru_business_check.service.arbitration_service import (
    ArbitrationBlocked,
    ArbitrationCaptchaRequired,
    ArbitrationError,
    fetch_arbitration_cases,
)


def _run(coro):
    return asyncio.run(coro)


class TestBlockedAndCaptchaDetection:
    def test_a_451_from_ddos_guard_raises_a_clean_blocked_error(self, patch_httpx_transport):
        def handler(request):
            return httpx.Response(
                451, headers={"server": "ddos-guard"}, html="<html>Доступ заблокирован</html>"
            )

        patch_httpx_transport(handler)

        with pytest.raises(ArbitrationBlocked, match="ограничил доступ"):
            _run(fetch_arbitration_cases("7712345678"))

    def test_a_403_is_also_treated_as_blocked_not_a_raw_http_error(self, patch_httpx_transport):
        patch_httpx_transport(lambda request: httpx.Response(403, text="Forbidden"))

        with pytest.raises(ArbitrationBlocked):
            _run(fetch_arbitration_cases("7712345678"))

    def test_captcha_required_flag_in_a_200_response_raises_captcha_error(
        self, patch_httpx_transport
    ):
        patch_httpx_transport(lambda request: httpx.Response(200, json={"CaptchaRequired": True}))

        with pytest.raises(ArbitrationCaptchaRequired, match="капчу"):
            _run(fetch_arbitration_cases("7712345678"))

    def test_an_unrelated_server_error_raises_a_clean_error_not_the_raw_httpx_exception(
        self, patch_httpx_transport
    ):
        patch_httpx_transport(lambda request: httpx.Response(500, text="internal error"))

        with pytest.raises(ArbitrationError, match="HTTP 500"):
            _run(fetch_arbitration_cases("7712345678"))


class TestSuccessPath:
    def test_returns_parsed_cases_and_raw_payload_on_success(self, patch_httpx_transport):
        payload = {
            "Success": True,
            "Result": {
                "Items": [
                    {
                        "CaseId": "abc",
                        "CaseNumber": "A1",
                        "Sides": [{"Inn": "7712345678", "Role": "Ответчик"}],
                    }
                ]
            },
        }
        patch_httpx_transport(lambda request: httpx.Response(200, json=payload))

        cases, raw = _run(fetch_arbitration_cases("7712345678"))

        assert cases == [
            {
                "case_number": "A1",
                "date_registered": None,
                "role": "defendant",
                "status": None,
                "court": None,
                "claim_amount": None,
                "case_url": "https://kad.arbitr.ru/Card/abc",
            }
        ]
        assert "A1" in raw

    def test_empty_inn_short_circuits_without_a_network_call(self, patch_httpx_transport):
        def fail_handler(request):
            raise AssertionError("should not have made a request")

        patch_httpx_transport(fail_handler)

        cases, raw = _run(fetch_arbitration_cases(""))

        assert cases == []
        assert raw == ""
