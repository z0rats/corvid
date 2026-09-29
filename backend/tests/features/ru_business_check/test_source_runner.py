"""`source_runner` - the one seam every post-ЕГРЮЛ source goes through - plus the scan-level
guarantee it exists for: any source failing for any network/parse reason is "not checked",
never a failed scan."""

import json

import httpx
import pytest

from app.features.ru_business_check.service import ru_business_check_service as svc
from app.features.ru_business_check.service.source_runner import (
    Source,
    SourceContext,
    empty_fields,
    run_source,
    store_results,
)
from tests.features.ru_business_check.scan_harness import as_async as _async
from tests.features.ru_business_check.scan_harness import run as _run
from tests.features.ru_business_check.scan_harness import start as _start


class SourceError(ValueError):
    pass


LEGAL = SourceContext(inn="7712345678", director="Иванов Иван Иванович", is_individual=False)


def _source(fetch, **kwargs):
    return Source("s", fetch, SourceError, **kwargs)


def _raising(exc):
    async def fetch(subject, ctx):
        raise exc

    return fetch


class TestRunSource:
    def test_success_is_checked(self):
        result = _run(run_source(_source(_async(lambda subject, ctx: ({"ok": 1}, "raw"))), LEGAL))
        assert (result.status, result.data, result.raw, result.checked) == (
            "checked",
            {"ok": 1},
            "raw",
            True,
        )

    @pytest.mark.parametrize(
        "exc",
        [
            SourceError("blocked"),
            httpx.ConnectError("refused"),
            httpx.ReadTimeout("slow"),
            httpx.HTTPStatusError(
                "503",
                request=httpx.Request("GET", "https://x"),
                response=httpx.Response(503),
            ),
            json.JSONDecodeError("bad", "doc", 0),
        ],
    )
    def test_any_network_or_parse_failure_is_failed_with_the_empty_result(self, exc):
        source = _source(_raising(exc), empty=lambda: {"checked": False})
        result = _run(run_source(source, LEGAL))
        assert (result.status, result.data, result.raw, result.checked) == (
            "failed",
            {"checked": False},
            "",
            False,
        )

    def test_an_unrelated_exception_is_a_bug_and_propagates(self):
        with pytest.raises(KeyError):
            _run(run_source(_source(_raising(KeyError("x"))), LEGAL))

    def test_missing_subject_is_skipped_without_fetching(self):
        source = _source(_raising(AssertionError("must not be called")), needs="director")
        ctx = SourceContext(inn="7712345678", director=None, is_individual=False)
        result = _run(run_source(source, ctx))
        assert (result.status, result.data, result.raw) == ("skipped", None, None)

    def test_not_applicable_to_an_individual(self):
        source = _source(
            _raising(AssertionError("must not be called")),
            not_applicable_to_individual=lambda: {"not_applicable": "ИП"},
        )
        ctx = SourceContext(inn="771234567890", director=None, is_individual=True)
        result = _run(run_source(source, ctx))
        assert (result.status, result.data) == ("not_applicable", {"not_applicable": "ИП"})

    def test_incomplete_keeps_data_but_is_not_checked(self):
        source = _source(
            _async(lambda subject, ctx: ({"partial": True}, "raw")),
            is_complete=lambda data, ctx: False,
        )
        result = _run(run_source(source, LEGAL))
        assert (result.status, result.data, result.checked) == (
            "incomplete",
            {"partial": True},
            False,
        )


class TestStoreResults:
    def test_dedicated_columns_and_extra_data(self):
        sources = [
            Source("a", None, SourceError, data_column="a_data", raw_column="a_raw", empty=dict),
            Source("b", None, SourceError),
            Source("c", None, SourceError),
        ]
        from app.features.ru_business_check.service.source_runner import SourceResult

        fields = store_results(
            sources,
            [
                SourceResult("a", "failed", {}, ""),
                SourceResult("b", "checked", {"x": 1}, "b raw"),
                SourceResult("c", "failed", None, None),
            ],
        )
        assert fields["a_data"] == {} and fields["a_raw"] == ""
        assert fields["extra_data"] == {"b": {"x": 1}}
        assert fields["extra_raw"] == {"b": "b raw"}

    def test_empty_fields_cover_every_dedicated_column(self):
        fields = empty_fields(svc._sources())
        for column in ("disqualification_result", "arbitration_data", "fedresurs_data", "rnp_data"):
            assert fields[column]["checked"] is False


class TestScanSurvivesTransportErrors:
    """Regression: a source fetcher that lets `httpx.ConnectError` escape (bare
    `raise_for_status()`/`client.get`) used to fail the whole scan as a bug."""

    @pytest.mark.parametrize(
        ("fetcher", "source_key"),
        [
            ("check_disqualified", "disqualified_persons"),
            ("fetch_arbitration_cases", "arbitration"),
            ("fetch_pb_nalog_profile", "pb_nalog"),
            ("fetch_gir_bo_financials", "gir_bo"),
        ],
    )
    def test_a_connect_error_marks_only_that_source_unchecked(
        self, monkeypatch, fake_db, captured, fetcher, source_key
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": "Иванов Иван Иванович",
            "ogrn": "1234567890123",
            "inn": "7712345678",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "r")))
        monkeypatch.setattr(
            svc,
            "check_disqualified",
            _async(
                lambda name: (
                    {
                        "checked": True,
                        "matched": False,
                        "requires_manual_review": False,
                        "matches": [],
                    },
                    "",
                )
            ),
        )

        async def refused(*args, **kwargs):
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(svc, fetcher, refused)
        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert source_key not in outcome.fields["checked_sources"]
        assert source_key in outcome.fields["pending_sources"]
        assert "egrul" in outcome.fields["checked_sources"]

    def test_egrul_transport_error_is_an_expected_egrul_failure(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.egrul_service import EgrulError

        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )

        async def refused(query):
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(svc, "fetch_egrul_extract", refused)
        _start()
        with pytest.raises(EgrulError):
            _run(captured["run_work"](123))
        assert EgrulError in captured["expected_exceptions"]
