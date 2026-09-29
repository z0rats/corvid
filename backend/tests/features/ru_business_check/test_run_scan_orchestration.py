"""run_scan_task's own orchestration logic (cache lookup, ЕГРЮЛ -> РДЛ -> flag-engine
pipeline, run_work/feature_name plumbing into ScanRun) - network calls, DB session, and
ScanRun.execute itself are all mocked out here.

ScanRun.execute's own lifecycle (create running row -> started -> terminal event + mark
row) is covered generically, against real tables, by tests/core/scans/test_run.py - not
this module's concern. What's specific to ru_business_check and worth testing here is
only what run_scan_task itself builds: the run_work closure's cache-hit short-circuit,
its mapping of a fresh ЕГРЮЛ+РДЛ result into a ScanOutcome, and that it's handed to
ScanRun.execute() with the right feature_name/model/create_fields/cancellable.
"""

import pytest

from app.core.scans.cancellable import TaskCancellable
from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch
from app.features.ru_business_check.service import ru_business_check_service as svc
from tests.features.ru_business_check.scan_harness import FakeCachedRow
from tests.features.ru_business_check.scan_harness import as_async as _async
from tests.features.ru_business_check.scan_harness import run as _run
from tests.features.ru_business_check.scan_harness import start as _start


class TestRunScanTaskDispatch:
    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, fake_db, captured):
        _start(query=" 7712345678 ")

        assert captured["feature_name"] == "ru_business_check"
        assert captured["model"] is RuBusinessCheckSearch
        assert captured["create_fields"] == {"query": "7712345678"}
        assert captured["started_fields"] == {"query": "7712345678"}
        assert isinstance(captured["cancellable"], TaskCancellable)


class TestRunWorkCacheHit:
    def test_serves_cached_result_without_hitting_sources(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc,
            "find_recent_completed_search_by_query",
            _async(lambda db, query, max_age: FakeCachedRow()),
        )

        called = {"egrul": False, "disq": False}

        async def fail_egrul(query):
            called["egrul"] = True

        async def fail_disq(name):
            called["disq"] = True

        monkeypatch.setattr(svc, "fetch_egrul_extract", fail_egrul)
        monkeypatch.setattr(svc, "check_disqualified", fail_disq)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called == {"egrul": False, "disq": False}
        assert outcome.fields["resolved_inn"] == "7712345678"
        assert outcome.fields["egrul_data"] == {"full_name": "cached co"}
        assert outcome.fields["risk_level"] == "low"

    def test_force_refresh_bypasses_cache(self, monkeypatch, fake_db, captured):
        cache_checked = {"called": False}

        async def fake_cache_lookup(db, query, max_age):
            cache_checked["called"] = True
            return FakeCachedRow()

        monkeypatch.setattr(svc, "find_recent_completed_search_by_query", fake_cache_lookup)
        monkeypatch.setattr(
            svc,
            "fetch_egrul_extract",
            _async(lambda query: ({"director_name": None, "ogrn": None, "inn": None}, "raw")),
        )
        monkeypatch.setattr(
            svc,
            "check_disqualified",
            _async(
                lambda name: (
                    {
                        "checked": False,
                        "matched": False,
                        "requires_manual_review": False,
                        "matches": [],
                    },
                    "",
                )
            ),
        )

        _start(force_refresh=True)
        _run(captured["run_work"](123))

        assert cache_checked["called"] is False


class TestRunWorkFreshScan:
    def test_assembles_outcome_from_egrul_and_disqualification_results(
        self, monkeypatch, fake_db, captured
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
        monkeypatch.setattr(
            svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "egrul raw"))
        )

        disq_result = {
            "checked": True,
            "matched": True,
            "requires_manual_review": False,
            "matches": [{"full_name": "Иванов Иван Иванович"}],
        }
        monkeypatch.setattr(
            svc, "check_disqualified", _async(lambda name: (disq_result, "disq raw"))
        )

        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["resolved_inn"] == "7712345678"
        assert outcome.fields["entity_type"] == "legal_entity"  # 13-digit ОГРН
        assert outcome.fields["risk_level"] == "high"  # confirmed disqualification is a hard flag
        assert any(f["code"] == "disqualified_confirmed" for f in outcome.fields["flags"])
        assert outcome.fields["checked_sources"] == [
            "egrul",
            "disqualified_persons",
            "arbitration",
            "fedresurs",
            "pb_nalog",
            "fedsfm",
            "zakupki_rnp",
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
        ]
        assert outcome.fields["pending_sources"] == ["fssp"]

    def test_skips_disqualification_check_when_no_director_name(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        monkeypatch.setattr(
            svc,
            "fetch_egrul_extract",
            _async(lambda query: ({"director_name": None, "ogrn": None, "inn": None}, "raw")),
        )

        called = {"disq": False}

        async def fail_disq(name):
            called["disq"] = True

        monkeypatch.setattr(svc, "check_disqualified", fail_disq)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called["disq"] is False
        assert outcome.fields["disqualification_result"]["checked"] is False

    def test_individual_entrepreneur_detected_from_15_digit_ogrnip(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "123456789012345",
            "inn": "771234567890",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["entity_type"] == "individual_entrepreneur"


class TestRunWorkArbitration:
    def test_fetches_arbitration_cases_by_resolved_inn(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "1234567890123",
            "inn": "7712345678",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        captured_inn = {}

        async def fake_arbitration(inn):
            captured_inn["inn"] = inn
            return [
                {
                    "case_number": "A1",
                    "role": "defendant",
                    "status": "Рассмотрение",
                    "claim_amount": None,
                }
            ], "arb raw"

        monkeypatch.setattr(svc, "fetch_arbitration_cases", fake_arbitration)

        _start()
        outcome = _run(captured["run_work"](123))

        assert captured_inn["inn"] == "7712345678"
        assert outcome.fields["arbitration_data"] == {
            "checked": True,
            "cases": [
                {
                    "case_number": "A1",
                    "role": "defendant",
                    "status": "Рассмотрение",
                    "claim_amount": None,
                }
            ],
        }
        assert outcome.fields["arbitration_raw"] == "arb raw"

    def test_skips_arbitration_when_no_resolved_inn(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        called = {"arbitration": False}

        async def fail_arbitration(inn):
            called["arbitration"] = True

        monkeypatch.setattr(svc, "fetch_arbitration_cases", fail_arbitration)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called["arbitration"] is False
        assert outcome.fields["arbitration_data"] == {"checked": False, "cases": []}

    def test_arbitration_flags_feed_into_the_overall_risk_level(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "1234567890123",
            "inn": "7712345678",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        many_cases = [
            {
                "case_number": f"A{i}",
                "role": "defendant",
                "status": "Рассмотрение",
                "claim_amount": None,
            }
            for i in range(3)
        ]
        monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: (many_cases, "raw")))

        _start()
        outcome = _run(captured["run_work"](123))

        assert any(
            f["code"] == "significant_or_multiple_claims_as_defendant"
            for f in outcome.fields["flags"]
        )
        assert outcome.fields["risk_level"] == "medium"


class TestRunWorkAmbiguousMatch:
    def test_ambiguous_match_completes_with_candidates_instead_of_failing(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.egrul_service import EgrulAmbiguousMatch

        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )

        candidates = [
            {"name": "ООО Ромашка №1", "inn": "1"},
            {"name": "ООО Ромашка №2", "inn": "2"},
        ]

        async def fake_fetch(query):
            raise EgrulAmbiguousMatch(candidates)

        monkeypatch.setattr(svc, "fetch_egrul_extract", fake_fetch)

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["candidates"] == candidates
        assert outcome.fields["egrul_data"] is None
        assert outcome.fields["resolved_inn"] is None
        assert outcome.fields["risk_level"] is None
        assert outcome.fields["checked_sources"] == []
        assert outcome.fields["pending_sources"] == [
            "egrul",
            "disqualified_persons",
            "arbitration",
            "fedresurs",
            "pb_nalog",
            "fedsfm",
            "zakupki_rnp",
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
            "fssp",
        ]

    def test_ambiguous_match_never_calls_disqualification_or_arbitration(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.egrul_service import EgrulAmbiguousMatch

        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )

        async def fake_fetch(query):
            raise EgrulAmbiguousMatch([{"name": "x"}])

        monkeypatch.setattr(svc, "fetch_egrul_extract", fake_fetch)

        called = {"disq": False, "arb": False}

        async def fail_disq(name):
            called["disq"] = True

        async def fail_arb(inn):
            called["arb"] = True

        monkeypatch.setattr(svc, "check_disqualified", fail_disq)
        monkeypatch.setattr(svc, "fetch_arbitration_cases", fail_arb)

        _start()
        _run(captured["run_work"](123))

        assert called == {"disq": False, "arb": False}


class TestRunWorkErrorHandling:
    def test_a_bare_timeout_error_is_rewritten_with_a_friendly_message(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )

        async def fake_fetch(query):
            raise TimeoutError()

        monkeypatch.setattr(svc, "fetch_egrul_extract", fake_fetch)

        _start()
        with pytest.raises(TimeoutError, match="Проверка заняла слишком много времени"):
            _run(captured["run_work"](123))

    def test_egrul_error_propagates_unwrapped(self, monkeypatch, fake_db, captured):
        from app.features.ru_business_check.service.egrul_service import EgrulError

        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )

        async def fake_fetch(query):
            raise EgrulError("Ничего не найдено")

        monkeypatch.setattr(svc, "fetch_egrul_extract", fake_fetch)

        _start()
        with pytest.raises(EgrulError, match="Ничего не найдено"):
            _run(captured["run_work"](123))
