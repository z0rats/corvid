import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.dork_runner.config.dork_templates import get_templates_for_target_type
from app.features.dork_runner.schemas.dork_schemas import DorkRunRequest
from app.features.dork_runner.service import dork_query_service
from app.features.dork_runner.service.dork_query_service import _resolve_templates
from app.features.dork_runner.service.engines import duckduckgo_engine
from app.features.dork_runner.service.engines.base import RawResult


def _run(coro):
    return asyncio.run(coro)


class TestResolveTemplates:
    def test_returns_all_templates_applicable_to_the_target_type_by_default(self):
        request = DorkRunRequest(target="example.com", target_type="domain")

        templates = _resolve_templates(request)

        expected_keys = {t.key for t in get_templates_for_target_type("domain")}
        assert {t.key for t in templates} == expected_keys

    def test_narrows_to_the_requested_template_keys(self):
        request = DorkRunRequest(
            target="example.com",
            target_type="domain",
            template_keys=["site_search", "filetype_pdf"],
        )

        templates = _resolve_templates(request)

        assert {t.key for t in templates} == {"site_search", "filetype_pdf"}

    def test_rejects_a_template_key_not_applicable_to_the_target_type(self):
        # linkedin_profile only applies to "username", not "domain".
        request = DorkRunRequest(
            target="example.com", target_type="domain", template_keys=["linkedin_profile"]
        )

        with pytest.raises(AppHTTPException) as exc_info:
            _resolve_templates(request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "DORK_INVALID_TEMPLATE"

    def test_caps_the_template_count_at_max_queries_per_run(self, monkeypatch):
        monkeypatch.setattr(dork_query_service, "MAX_QUERIES_PER_RUN", 2)
        request = DorkRunRequest(target="example.com", target_type="domain")

        templates = _resolve_templates(request)

        assert len(templates) == 2


class TestPerformDorkRun:
    @pytest.fixture(autouse=True)
    def _no_real_delay(self, monkeypatch):
        # perform_dork_run awaits a real politeness delay between queries -
        # replace it with a no-op so the test suite doesn't actually wait.
        async def _instant_sleep(_seconds):
            return None

        monkeypatch.setattr(dork_query_service.asyncio, "sleep", _instant_sleep)

    def test_aggregates_results_across_all_resolved_templates(self, monkeypatch):
        async def fake_search(query):
            return [
                RawResult(title="Result for " + query, url="https://example.com/x", snippet="...")
            ]

        monkeypatch.setattr(duckduckgo_engine, "search", fake_search)
        request = DorkRunRequest(
            target="example.com",
            target_type="domain",
            engine="duckduckgo",
            template_keys=["site_search", "filetype_pdf"],
        )

        response = _run(dork_query_service.perform_dork_run(request))

        assert response.queries_run == 2
        assert response.total_results == 2
        assert response.errors == []
        assert {r.template_key for r in response.results} == {"site_search", "filetype_pdf"}

    def test_a_failing_query_is_recorded_as_a_non_fatal_error_and_others_still_run(
        self, monkeypatch
    ):
        calls = []

        async def flaky_search(query):
            calls.append(query)
            if "filetype:pdf" in query:
                raise RuntimeError("engine blocked the request")
            return [RawResult(title="ok", url="https://example.com", snippet="")]

        monkeypatch.setattr(duckduckgo_engine, "search", flaky_search)
        request = DorkRunRequest(
            target="example.com",
            target_type="domain",
            engine="duckduckgo",
            template_keys=["site_search", "filetype_pdf"],
        )

        response = _run(dork_query_service.perform_dork_run(request))

        assert len(calls) == 2  # both queries attempted despite the first failing
        assert response.total_results == 1
        assert len(response.errors) == 1
        assert "filetype_pdf" in response.errors[0]

    def test_waits_between_queries_but_not_after_the_last_one(self, monkeypatch):
        sleep_calls = []

        async def _tracking_sleep(seconds):
            sleep_calls.append(seconds)

        monkeypatch.setattr(dork_query_service.asyncio, "sleep", _tracking_sleep)

        async def fake_search(query):
            return []

        monkeypatch.setattr(duckduckgo_engine, "search", fake_search)
        request = DorkRunRequest(
            target="example.com",
            target_type="domain",
            engine="duckduckgo",
            template_keys=["site_search", "filetype_pdf", "filetype_xlsx"],
        )

        _run(dork_query_service.perform_dork_run(request))

        assert len(sleep_calls) == 2  # delay between 1st/2nd and 2nd/3rd, not after the 3rd

    def test_an_unexpected_error_outside_the_per_query_try_is_wrapped_in_a_clean_500(
        self, monkeypatch
    ):
        async def _broken_sleep(_seconds):
            raise RuntimeError("something broke outside the per-query handling")

        monkeypatch.setattr(dork_query_service.asyncio, "sleep", _broken_sleep)

        async def fake_search(query):
            return []

        monkeypatch.setattr(duckduckgo_engine, "search", fake_search)
        request = DorkRunRequest(
            target="example.com",
            target_type="domain",
            engine="duckduckgo",
            template_keys=["site_search", "filetype_pdf"],
        )

        with pytest.raises(AppHTTPException) as exc_info:
            _run(dork_query_service.perform_dork_run(request))

        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "DORK_RUN_ERROR"
