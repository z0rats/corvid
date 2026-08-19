"""pb_nalog_service's network behavior (the two two-step async job flows), using
httpx.MockTransport (same pattern as test_arbitration_search.py/test_fedresurs_search.py)
so status-code handling and the poll loop run for real against canned responses.
`asyncio.sleep` is patched out so the poll loop's real 1.5s waits don't slow tests down.
"""

import asyncio

import httpx
import pytest

from app.features.ru_business_check.service import pb_nalog_service
from app.features.ru_business_check.service.pb_nalog_service import (
    PbNalogCaptchaRequired,
    PbNalogError,
    PbNalogRateLimited,
    fetch_pb_nalog_profile,
)

INN = "7707083893"


def _run(coro):
    return asyncio.run(coro)


_real_sleep = asyncio.sleep


@pytest.fixture
def _patch_transport(patch_httpx_transport, monkeypatch):
    """Composes the shared `patch_httpx_transport` adapter with a local patch this
    feature alone needs: the poll loop's real 1.5s waits are collapsed so tests
    don't slow down."""

    def _patch(handler):
        patch_httpx_transport(handler)
        monkeypatch.setattr(pb_nalog_service.asyncio, "sleep", lambda *_a, **_k: _real_sleep(0))

    return _patch


class TestErrorHandling:
    def test_a_pbsearchcaptcha_error_raises_a_clean_captcha_error(self, _patch_transport):
        def handler(request):
            return httpx.Response(400, json={"ERRORS": {"pbSearchCaptcha": ["x"]}})

        _patch_transport(handler)

        with pytest.raises(PbNalogCaptchaRequired, match="капчу"):
            _run(fetch_pb_nalog_profile(INN, is_individual=False))

    def test_a_pbratelimit_error_raises_a_clean_rate_limit_error(self, _patch_transport):
        def handler(request):
            return httpx.Response(429, json={"ERRORS": {"pbRateLimit": ["x"]}})

        _patch_transport(handler)

        with pytest.raises(PbNalogRateLimited, match="лимит"):
            _run(fetch_pb_nalog_profile(INN, is_individual=False))

    def test_an_inline_captcharequired_flag_on_a_200_raises_a_clean_error(self, _patch_transport):
        def handler(request):
            return httpx.Response(200, json={"id": "x", "captchaRequired": True})

        _patch_transport(handler)

        with pytest.raises(PbNalogCaptchaRequired):
            _run(fetch_pb_nalog_profile(INN, is_individual=False))

    def test_an_unrelated_server_error_raises_a_clean_error_not_a_raw_httpx_exception(
        self, _patch_transport
    ):
        def handler(request):
            return httpx.Response(500, text="internal error")

        _patch_transport(handler)

        with pytest.raises(PbNalogError, match="HTTP 500"):
            _run(fetch_pb_nalog_profile(INN, is_individual=False))

    def test_polling_forever_null_eventually_raises_a_clean_timeout_error(self, _patch_transport):
        def handler(request):
            if b"queryAll" in (request.content or b""):
                return httpx.Response(200, json={"id": "job1", "captchaRequired": False})
            return httpx.Response(
                200, content=b"null", headers={"content-type": "application/json"}
            )

        _patch_transport(handler)

        with pytest.raises(PbNalogError, match="не ответил"):
            _run(fetch_pb_nalog_profile(INN, is_individual=False))


class TestSuccessPath:
    def test_full_flow_returns_parsed_result_and_raw_payload(self, _patch_transport):
        calls = {"search_submit": 0, "search_poll": 0, "detail_submit": 0, "detail_poll": 0}

        def handler(request):
            body = (request.content or b"").decode()
            if "search-proc" in str(request.url):
                if "queryAll" in body:
                    calls["search_submit"] += 1
                    return httpx.Response(200, json={"id": "search-job", "captchaRequired": False})
                calls["search_poll"] += 1
                return httpx.Response(
                    200,
                    json={
                        "ul": {"data": [{"inn": INN, "token": "TOK123"}], "rowCount": 1},
                        "ip": {"data": [], "rowCount": 0},
                    },
                )
            if "company-proc" in str(request.url):
                if "get-request" in body:
                    calls["detail_submit"] += 1
                    return httpx.Response(
                        200, json={"id": "detail-job", "captchaRequired": False, "token": "TOK456"}
                    )
                calls["detail_poll"] += 1
                return httpx.Response(
                    200,
                    json={
                        "is_p_ruk": True,
                        "masaddress": [{"massinn": "111", "massnamep": "ООО Сосед"}],
                    },
                )
            raise AssertionError(f"unexpected URL: {request.url}")

        _patch_transport(handler)

        result, raw = _run(fetch_pb_nalog_profile(INN, is_individual=False))

        assert calls == {"search_submit": 1, "search_poll": 1, "detail_submit": 1, "detail_poll": 1}
        assert result["checked"] is True
        assert result["found"] is True
        assert result["mass_address_count"] == 1
        assert (
            result["profile_url"]
            == f"https://pb.nalog.ru/search.html#mode=search-all&queryAll={INN}"
        )
        assert "Сосед" in raw

    def test_the_detail_poll_uses_the_new_token_from_get_request_not_the_search_token(
        self, _patch_transport
    ):
        seen_tokens = []

        def handler(request):
            body = (request.content or b"").decode()
            if "search-proc" in str(request.url):
                if "queryAll" in body:
                    return httpx.Response(200, json={"id": "search-job", "captchaRequired": False})
                return httpx.Response(
                    200,
                    json={
                        "ul": {"data": [{"inn": INN, "token": "SEARCH-TOKEN"}], "rowCount": 1},
                        "ip": {"data": [], "rowCount": 0},
                    },
                )
            if "get-request" in body:
                return httpx.Response(
                    200,
                    json={"id": "detail-job", "captchaRequired": False, "token": "DETAIL-TOKEN"},
                )
            # detail poll
            if "token=DETAIL-TOKEN" in body:
                seen_tokens.append("DETAIL-TOKEN")
            elif "token=SEARCH-TOKEN" in body:
                seen_tokens.append("SEARCH-TOKEN")
            return httpx.Response(200, json={})

        _patch_transport(handler)

        _run(fetch_pb_nalog_profile(INN, is_individual=False))

        assert seen_tokens == ["DETAIL-TOKEN"]

    def test_no_matching_search_row_is_a_clean_not_found_result_not_an_error(
        self, _patch_transport
    ):
        def handler(request):
            body = (request.content or b"").decode()
            if "queryAll" in body:
                return httpx.Response(200, json={"id": "search-job", "captchaRequired": False})
            return httpx.Response(
                200, json={"ul": {"data": [], "rowCount": 0}, "ip": {"data": [], "rowCount": 0}}
            )

        _patch_transport(handler)

        result, raw = _run(fetch_pb_nalog_profile(INN, is_individual=False))

        assert result["checked"] is True
        assert result["found"] is False
        assert result["mass_address_count"] == 0

    def test_empty_inn_short_circuits_without_a_network_call(self, _patch_transport):
        def fail_handler(request):
            raise AssertionError("should not have made a request")

        _patch_transport(fail_handler)

        result, raw = _run(fetch_pb_nalog_profile("", is_individual=False))

        assert result["checked"] is False
        assert raw == ""
