"""`run_scan_task` orchestration of the verdict semantics and the `extra_data` / local-dump
sources (see docs/adr/0014-*.md): incomplete verdicts, Федресурс publications, cache rules,
ГИР БО/МСП, the ФНС/ЦБ/OFAC lookups, payload digests. Mocked like
test_run_scan_orchestration.py - no network, no real DB unless a test builds one."""

import datetime

import pytest

from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch
from app.features.ru_business_check.service import ru_business_check_service as svc
from tests.features.ru_business_check.scan_harness import FakeCachedRow
from tests.features.ru_business_check.scan_harness import as_async as _async
from tests.features.ru_business_check.scan_harness import run as _run
from tests.features.ru_business_check.scan_harness import start as _start


class TestRunWorkIncompleteVerdict:
    def _egrul(self, monkeypatch):
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

    @pytest.mark.parametrize("failing_source", ["fedresurs", "zakupki_rnp"])
    def test_a_failed_required_source_never_yields_a_low_verdict(
        self, failing_source, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.fedresurs_service import FedresursError
        from app.features.ru_business_check.service.zakupki_rnp_service import ZakupkiRnpError

        self._egrul(monkeypatch)
        target, error = {
            "fedresurs": ("fetch_fedresurs_status", FedresursError("blocked")),
            "zakupki_rnp": ("fetch_rnp_entries", ZakupkiRnpError("down")),
        }[failing_source]

        async def failing(*args, **kwargs):
            raise error

        monkeypatch.setattr(svc, target, failing)

        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["flags"] == []
        assert failing_source in outcome.fields["pending_sources"]
        assert outcome.fields["risk_level"] == "incomplete"

    def test_all_required_sources_checked_and_nothing_found_is_low(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch)

        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["risk_level"] == "low"

    def test_an_unresolved_inn_skips_required_sources_and_is_incomplete(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["risk_level"] == "incomplete"


class TestRunWorkExtraSources:
    def _egrul(self, monkeypatch, inn="7712345678"):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "1234567890123",
            "inn": inn,
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

    def test_results_and_raw_payloads_land_in_extra_columns_keyed_by_source(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch)
        _start()
        outcome = _run(captured["run_work"](123))

        assert set(outcome.fields["extra_data"]) == {
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
        }
        # The dump is a local lookup: no remote payload to keep.
        assert set(outcome.fields["extra_raw"]) == {"gir_bo", "msp"}
        assert {"gir_bo", "msp"} <= set(outcome.fields["checked_sources"])

    def test_one_failing_extra_source_does_not_discard_the_others(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.gir_bo_service import GirBoError

        self._egrul(monkeypatch)

        async def failing(inn, is_individual):
            raise GirBoError("bo.nalog.gov.ru недоступен")

        monkeypatch.setattr(svc, "fetch_gir_bo_financials", failing)
        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert set(outcome.fields["extra_data"]) == {
            "msp",
            "disqualified_dump",
            "cbr_warning",
            "ofac_sdn",
        }
        assert "gir_bo" in outcome.fields["pending_sources"]
        assert "msp" in outcome.fields["checked_sources"]

    def test_financial_flags_flow_from_gir_bo_into_the_verdict(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch)
        years = [
            {
                "year": 2025,
                "revenue": 100.0,
                "assets": 100.0,
                "equity": 1.0,
                "current_assets": 90.0,
                "current_liabilities": 50.0,
            }
        ]
        monkeypatch.setattr(
            svc,
            "fetch_gir_bo_financials",
            _async(
                lambda inn, is_individual: ({"checked": True, "found": True, "years": years}, "")
            ),
        )
        _start()
        outcome = _run(captured["run_work"](123))

        assert [f["code"] for f in outcome.fields["flags"]] == ["low_equity_ratio"]
        assert outcome.fields["risk_level"] == "medium"

    def test_extra_sources_are_skipped_without_a_resolved_inn(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        async def fail(inn, is_individual):
            raise AssertionError("must not be called")

        monkeypatch.setattr(svc, "fetch_gir_bo_financials", fail)
        monkeypatch.setattr(svc, "fetch_msp_status", fail)
        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["extra_data"] == {}


class TestRunWorkRawDigests:
    def test_every_captured_payload_is_fingerprinted_at_scan_time(
        self, monkeypatch, fake_db, captured
    ):
        import hashlib

        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "1234567890123",
            "inn": "7712345678",
            "registration_date": None,
        }
        monkeypatch.setattr(
            svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "egrul raw text"))
        )
        monkeypatch.setattr(svc, "fetch_rnp_entries", _async(lambda inn: ([], "rnp raw")))
        monkeypatch.setattr(
            svc,
            "fetch_msp_status",
            _async(lambda inn, is_individual: ({"checked": True, "found": False}, "msp raw")),
        )

        _start()
        outcome = _run(captured["run_work"](123))

        digests = outcome.fields["raw_sha256"]
        assert digests["egrul"] == hashlib.sha256(b"egrul raw text").hexdigest()
        assert digests["zakupki_rnp"] == hashlib.sha256(b"rnp raw").hexdigest()
        assert digests["msp"] == hashlib.sha256(b"msp raw").hexdigest()
        # Sources that produced no payload (the fixtures return "") are not fingerprinted.
        assert "arbitration" not in digests

    def test_a_cached_result_keeps_its_original_digests(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc,
            "find_recent_completed_search_by_query",
            _async(lambda db, query, max_age: FakeCachedRow()),
        )
        _start()
        outcome = _run(captured["run_work"](123))
        assert outcome.fields["raw_sha256"] == {"egrul": "cached digest"}


class TestRunWorkDisqualifiedDump:
    def _egrul(self, monkeypatch, director="ИВАНОВ ИВАН ИВАНОВИЧ"):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": director,
            "ogrn": "1234567890123",
            "inn": "7712345678",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))
        monkeypatch.setattr(
            svc,
            "check_disqualified",
            _async(
                lambda name: (
                    {
                        "checked": True,
                        "matched": True,
                        "requires_manual_review": True,
                        "matches": [{"full_name": name}],
                    },
                    "raw",
                )
            ),
        )

    def test_a_confirmed_dump_match_replaces_the_name_only_soft_flag_with_a_hard_one(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch)
        seen = {}

        async def fake_lookup(db, inn, director_name):
            seen["args"] = (inn, director_name)
            record = {
                "record_number": "1",
                "full_name": "ИВАНОВ ИВАН ИВАНОВИЧ",
                "active": True,
                "same_company": True,
                "start_date": "2025-01-01",
                "end_date": "2027-01-01",
            }
            return {
                "checked": True,
                "dump_date": "2026-09-20",
                "director_confirmed": True,
                "director_records": [record],
                "company_records": [record],
            }

        monkeypatch.setattr(svc, "lookup_dump", fake_lookup)
        _start()
        outcome = _run(captured["run_work"](123))

        assert seen["args"] == ("7712345678", "ИВАНОВ ИВАН ИВАНОВИЧ")
        codes = [f["code"] for f in outcome.fields["flags"]]
        assert "disqualified_confirmed" in codes
        assert "disqualified_possible_match" not in codes
        assert outcome.fields["risk_level"] == "high"
        assert "disqualified_dump" in outcome.fields["checked_sources"]

    def test_no_dump_loaded_leaves_the_online_soft_flag_and_marks_the_source_pending(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.disqualified_dump_service import (
            DisqualifiedDumpError,
        )

        self._egrul(monkeypatch)

        async def not_loaded(db, inn, director_name):
            raise DisqualifiedDumpError("выгрузка ещё не загружена")

        monkeypatch.setattr(svc, "lookup_dump", not_loaded)
        _start()
        outcome = _run(captured["run_work"](123))

        assert [f["code"] for f in outcome.fields["flags"]] == ["disqualified_possible_match"]
        assert "disqualified_dump" in outcome.fields["pending_sources"]
        assert "disqualified_dump" not in outcome.fields["extra_data"]


class TestRunWorkCbrWarning:
    def _egrul(self, monkeypatch, ogrn="1234567890123", inn="7712345678"):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": ogrn, "inn": inn, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

    def test_a_listed_company_raises_the_regulators_soft_flag(self, monkeypatch, fake_db, captured):
        self._egrul(monkeypatch)
        record = {"cbr_id": 1, "sign": "Признаки нелегального кредитора", "listed_at": "2025-01-01"}
        monkeypatch.setattr(
            svc,
            "lookup_cbr_list",
            _async(lambda db, inn: {"checked": True, "as_of": "2026-09-28", "records": [record]}),
        )
        _start()
        outcome = _run(captured["run_work"](123))

        assert [f["code"] for f in outcome.fields["flags"]] == ["cbr_warning_list"]
        assert "cbr_warning" in outcome.fields["checked_sources"]

    def test_an_individual_entrepreneur_is_checked_as_not_applicable_without_a_lookup(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch, ogrn="123456789012345", inn="771234567890")

        async def fail(db, inn):
            raise AssertionError("the list has no ИП ИНН - must not be called")

        monkeypatch.setattr(svc, "lookup_cbr_list", fail)
        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["extra_data"]["cbr_warning"]["not_applicable"]
        # Neither "checked" (nothing was looked up) nor "pending" (nothing can be).
        assert "cbr_warning" not in outcome.fields["checked_sources"]
        assert "cbr_warning" not in outcome.fields["pending_sources"]

    def test_no_list_loaded_marks_the_source_pending(self, monkeypatch, fake_db, captured):
        from app.features.ru_business_check.service.cbr_warning_service import CbrWarningError

        self._egrul(monkeypatch)

        async def not_loaded(db, inn):
            raise CbrWarningError("список ЦБ ещё не загружен")

        monkeypatch.setattr(svc, "lookup_cbr_list", not_loaded)
        _start()
        outcome = _run(captured["run_work"](123))

        assert "cbr_warning" in outcome.fields["pending_sources"]
        assert "cbr_warning" not in outcome.fields["extra_data"]


class TestRunWorkOfacSdn:
    def _egrul(self, monkeypatch, ogrn="1234567890123", inn="7712345678"):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": ogrn, "inn": inn, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

    def test_a_listed_company_raises_a_hard_flag(self, monkeypatch, fake_db, captured):
        self._egrul(monkeypatch)
        record = {"ent_num": 1, "name": "OOO X", "kind": "entity", "programs": "RUSSIA-EO14024"}
        monkeypatch.setattr(
            svc,
            "lookup_ofac_list",
            _async(lambda db, inn: {"checked": True, "as_of": "2026-09-28", "records": [record]}),
        )
        _start()
        outcome = _run(captured["run_work"](123))

        assert [f["code"] for f in outcome.fields["flags"]] == ["ofac_sdn_listed"]
        assert outcome.fields["risk_level"] == "high"

    def test_an_individual_entrepreneur_is_looked_up_by_their_12_digit_inn(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch, ogrn="123456789012345", inn="771234567890")
        seen = {}

        async def fake_lookup(db, inn):
            seen["inn"] = inn
            return {"checked": True, "as_of": "2026-09-28", "records": []}

        monkeypatch.setattr(svc, "lookup_ofac_list", fake_lookup)
        _start()
        outcome = _run(captured["run_work"](123))

        assert seen["inn"] == "771234567890"
        assert "ofac_sdn" in outcome.fields["checked_sources"]

    def test_no_list_loaded_marks_the_source_pending_not_clean(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.ofac_sdn_service import OfacSdnError

        self._egrul(monkeypatch)

        async def not_loaded(db, inn):
            raise OfacSdnError("список OFAC ещё не загружен")

        monkeypatch.setattr(svc, "lookup_ofac_list", not_loaded)
        _start()
        outcome = _run(captured["run_work"](123))

        assert "ofac_sdn" in outcome.fields["pending_sources"]
        assert "ofac_sdn" not in outcome.fields["extra_data"]


class TestRunWorkFedresursPublications:
    def _egrul(self, monkeypatch):
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

    def _fedresurs(self, **overrides):
        result = {
            "checked": True,
            "found": True,
            "status_text": "Действующее",
            "is_active_bankruptcy": False,
            "status_recognized": True,
            "profile_url": None,
            "publications_checked": False,
            "publications_note": "Сообщения Федресурса не проверены: blocked",
            "signals": [],
        }
        result.update(overrides)
        return result

    def test_unread_publications_make_the_source_unchecked_and_the_verdict_incomplete(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch)
        monkeypatch.setattr(
            svc,
            "fetch_fedresurs_status",
            _async(lambda inn, is_individual: (self._fedresurs(), "raw")),
        )
        _start()
        outcome = _run(captured["run_work"](123))

        assert "fedresurs" in outcome.fields["pending_sources"]
        # The status that *was* read is kept and shown.
        assert outcome.fields["fedresurs_data"]["status_text"] == "Действующее"
        assert outcome.fields["risk_level"] == "incomplete"

    def test_an_active_bankruptcy_stays_high_even_if_publications_failed(
        self, monkeypatch, fake_db, captured
    ):
        self._egrul(monkeypatch)
        result = self._fedresurs(is_active_bankruptcy=True, status_text="конкурсное производство")
        monkeypatch.setattr(
            svc, "fetch_fedresurs_status", _async(lambda inn, is_individual: (result, "raw"))
        )
        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["risk_level"] == "high"


class TestCacheExcludesIncomplete:
    def test_an_incomplete_scan_is_not_served_from_cache(self, make_session_factory):
        from app.features.ru_business_check.crud.ru_business_check_crud import (
            find_recent_completed_search_by_query,
        )

        factory = make_session_factory([RuBusinessCheckSearch.__table__])

        async def go():
            async with factory() as db:
                for risk in ("incomplete", None):
                    db.add(
                        RuBusinessCheckSearch(
                            query=f"q-{risk}", status="completed", risk_level=risk
                        )
                    )
                db.add(RuBusinessCheckSearch(query="q-low", status="completed", risk_level="low"))
                await db.commit()
                return [
                    await find_recent_completed_search_by_query(
                        db, q, max_age=datetime.timedelta(hours=24)
                    )
                    for q in ("q-incomplete", "q-None", "q-low")
                ]

        incomplete, ambiguous, low = _run(go())
        assert incomplete is None
        assert ambiguous is not None  # the disambiguation list is still cached
        assert low is not None


class TestCacheKeepsTheNewWebsite:
    def test_a_cache_hit_uses_the_requests_own_website(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc,
            "find_recent_completed_search_by_query",
            _async(lambda db, query, max_age: FakeCachedRow()),
        )
        _start(website=" new.example ")
        outcome = _run(captured["run_work"](123))
        assert outcome.fields["website"] == "new.example"

    def test_a_cache_hit_without_a_website_keeps_the_cached_one(
        self, monkeypatch, fake_db, captured
    ):
        row = FakeCachedRow()
        row.website = "old.example"
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: row)
        )
        _start()
        outcome = _run(captured["run_work"](123))
        assert outcome.fields["website"] == "old.example"
