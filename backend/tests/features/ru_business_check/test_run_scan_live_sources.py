"""`run_scan_task` orchestration of each dedicated live source (arbitration, Федресурс,
Прозрачный бизнес, ФедСФМ, РНП, website) and of one source failing without discarding the
others. Mocked like test_run_scan_orchestration.py - no network, no DB."""

from app.features.ru_business_check.service import ru_business_check_service as svc
from tests.features.ru_business_check.scan_harness import as_async as _async
from tests.features.ru_business_check.scan_harness import run as _run
from tests.features.ru_business_check.scan_harness import start as _start


class TestRunWorkPartialSourceFailure:
    """A single downstream source (РДЛ, арбитраж) failing - blocked, rate-limited,
    timed out - must not discard the ЕГРЮЛ data (or each other's data) that already
    succeeded. Regression coverage for a real bug: an earlier version let any
    ArbitrationError/DisqualifiedPersonsError propagate out of run_work entirely,
    turning a working scan into a hard 'failed' status and losing everything."""

    def test_arbitration_failure_still_completes_with_egrul_and_disqualification_data(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.arbitration_service import ArbitrationError

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
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        monkeypatch.setattr(
            svc, "check_disqualified", _async(lambda name: (disq_result, "disq raw"))
        )

        async def fake_arbitration(inn):
            raise ArbitrationError("kad.arbitr.ru временно ограничил доступ")

        monkeypatch.setattr(svc, "fetch_arbitration_cases", fake_arbitration)

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["egrul_data"] == egrul_data
        assert outcome.fields["disqualification_result"] == disq_result
        assert outcome.fields["arbitration_data"] == {"checked": False, "cases": []}
        assert outcome.fields["checked_sources"] == [
            "egrul",
            "disqualified_persons",
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
        assert "arbitration" in outcome.fields["pending_sources"]

    def test_disqualification_failure_still_completes_with_egrul_and_arbitration_data(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.disqualified_persons_service import (
            DisqualifiedPersonsError,
        )

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

        async def fake_disq(name):
            raise DisqualifiedPersonsError("service.nalog.ru недоступен")

        monkeypatch.setattr(svc, "check_disqualified", fake_disq)
        monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: ([], "arb raw")))

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["egrul_data"] == egrul_data
        assert outcome.fields["disqualification_result"]["checked"] is False
        assert outcome.fields["arbitration_data"] == {"checked": True, "cases": []}
        assert outcome.fields["checked_sources"] == [
            "egrul",
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
        assert "disqualified_persons" in outcome.fields["pending_sources"]

    def test_fedresurs_failure_still_completes_with_egrul_disq_and_arbitration_data(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.fedresurs_service import FedresursError

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
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        monkeypatch.setattr(
            svc, "check_disqualified", _async(lambda name: (disq_result, "disq raw"))
        )
        monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: ([], "arb raw")))

        async def fake_fedresurs(inn, is_individual):
            raise FedresursError("fedresurs.ru временно ограничил доступ")

        monkeypatch.setattr(svc, "fetch_fedresurs_status", fake_fedresurs)

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["egrul_data"] == egrul_data
        assert outcome.fields["disqualification_result"] == disq_result
        assert outcome.fields["arbitration_data"] == {"checked": True, "cases": []}
        assert outcome.fields["checked_sources"] == [
            "egrul",
            "disqualified_persons",
            "arbitration",
            "pb_nalog",
            "fedsfm",
            "zakupki_rnp",
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
        ]
        assert "fedresurs" in outcome.fields["pending_sources"]

    def test_pb_nalog_failure_still_completes_with_all_other_source_data(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.pb_nalog_service import PbNalogError

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
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        monkeypatch.setattr(
            svc, "check_disqualified", _async(lambda name: (disq_result, "disq raw"))
        )
        monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: ([], "arb raw")))

        async def fake_pb_nalog(inn, is_individual):
            raise PbNalogError("pb.nalog.ru временно ограничил доступ")

        monkeypatch.setattr(svc, "fetch_pb_nalog_profile", fake_pb_nalog)

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["egrul_data"] == egrul_data
        assert outcome.fields["disqualification_result"] == disq_result
        assert outcome.fields["arbitration_data"] == {"checked": True, "cases": []}
        assert outcome.fields["checked_sources"] == [
            "egrul",
            "disqualified_persons",
            "arbitration",
            "fedresurs",
            "fedsfm",
            "zakupki_rnp",
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
        ]
        assert "pb_nalog" in outcome.fields["pending_sources"]

    def test_fedsfm_failure_still_completes_with_all_other_source_data(
        self, monkeypatch, fake_db, captured
    ):
        from app.features.ru_business_check.service.fedsfm_service import FedsfmError

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
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        monkeypatch.setattr(
            svc, "check_disqualified", _async(lambda name: (disq_result, "disq raw"))
        )
        monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: ([], "arb raw")))

        async def fake_fedsfm(name):
            raise FedsfmError("fedsfm.ru недоступен")

        monkeypatch.setattr(svc, "check_terrorist_list", fake_fedsfm)

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["egrul_data"] == egrul_data
        assert outcome.fields["disqualification_result"] == disq_result
        assert outcome.fields["arbitration_data"] == {"checked": True, "cases": []}
        assert outcome.fields["checked_sources"] == [
            "egrul",
            "disqualified_persons",
            "arbitration",
            "fedresurs",
            "pb_nalog",
            "zakupki_rnp",
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
        ]
        assert "fedsfm" in outcome.fields["pending_sources"]

    def test_zakupki_rnp_failure_still_completes_with_all_other_source_data(
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
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        monkeypatch.setattr(
            svc, "check_disqualified", _async(lambda name: (disq_result, "disq raw"))
        )
        monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: ([], "arb raw")))

        async def fake_rnp(inn):
            raise svc.ZakupkiRnpError("zakupki.gov.ru недоступен")

        monkeypatch.setattr(svc, "fetch_rnp_entries", fake_rnp)

        _start()
        outcome = _run(captured["run_work"](123))  # must not raise

        assert outcome.fields["egrul_data"] == egrul_data
        assert outcome.fields["disqualification_result"] == disq_result
        assert outcome.fields["rnp_data"] == {"checked": False, "entries": []}
        assert outcome.fields["checked_sources"] == [
            "egrul",
            "disqualified_persons",
            "arbitration",
            "fedresurs",
            "pb_nalog",
            "fedsfm",
            "gir_bo",
            "msp",
            "disqualified_dump",
            "ofac_sdn",
            "cbr_warning",
        ]
        assert "zakupki_rnp" in outcome.fields["pending_sources"]


class TestRunWorkFedresurs:
    def test_fetches_fedresurs_status_by_resolved_inn(self, monkeypatch, fake_db, captured):
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

        captured_args = {}

        async def fake_fedresurs(inn, is_individual):
            captured_args["inn"] = inn
            captured_args["is_individual"] = is_individual
            return {
                "checked": True,
                "found": True,
                "status_text": "Действующее",
                "is_active_bankruptcy": False,
                "profile_url": "https://fedresurs.ru/company/abc",
                "publications_checked": True,
            }, "fedresurs raw"

        monkeypatch.setattr(svc, "fetch_fedresurs_status", fake_fedresurs)

        _start()
        outcome = _run(captured["run_work"](123))

        assert captured_args == {"inn": "7712345678", "is_individual": False}
        assert outcome.fields["fedresurs_data"]["status_text"] == "Действующее"
        assert outcome.fields["fedresurs_raw"] == "fedresurs raw"
        assert "fedresurs" in outcome.fields["checked_sources"]

    def test_uses_persons_lookup_for_individual_entrepreneurs(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "123456789012345",  # 15-digit ОГРНИП -> individual_entrepreneur
            "inn": "771234567890",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        captured_args = {}

        async def fake_fedresurs(inn, is_individual):
            captured_args["is_individual"] = is_individual
            return {
                "checked": True,
                "found": False,
                "status_text": None,
                "is_active_bankruptcy": False,
                "profile_url": None,
            }, ""

        monkeypatch.setattr(svc, "fetch_fedresurs_status", fake_fedresurs)

        _start()
        _run(captured["run_work"](123))

        assert captured_args["is_individual"] is True

    def test_skips_fedresurs_when_no_resolved_inn(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        called = {"fedresurs": False}

        async def fail_fedresurs(inn, is_individual):
            called["fedresurs"] = True

        monkeypatch.setattr(svc, "fetch_fedresurs_status", fail_fedresurs)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called["fedresurs"] is False
        assert outcome.fields["fedresurs_data"]["checked"] is False

    def test_active_bankruptcy_flag_feeds_into_the_overall_risk_level(
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

        async def fake_fedresurs(inn, is_individual):
            return {
                "checked": True,
                "found": True,
                "status_text": "Юридическое лицо признано несостоятельным (банкротом)",
                "is_active_bankruptcy": True,
                "profile_url": None,
            }, "raw"

        monkeypatch.setattr(svc, "fetch_fedresurs_status", fake_fedresurs)

        _start()
        outcome = _run(captured["run_work"](123))

        assert any(f["code"] == "active_bankruptcy" for f in outcome.fields["flags"])
        assert outcome.fields["risk_level"] == "high"


class TestRunWorkPbNalog:
    def test_fetches_pb_nalog_profile_by_resolved_inn(self, monkeypatch, fake_db, captured):
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

        captured_args = {}

        async def fake_pb_nalog(inn, is_individual):
            captured_args["inn"] = inn
            captured_args["is_individual"] = is_individual
            return {
                "checked": True,
                "found": True,
                "mass_address_count": 2,
                "mass_address_companies": [{"inn": "111", "name": "ООО Сосед"}],
                "profile_url": "https://pb.nalog.ru/search.html#mode=search-all&queryAll=7712345678",
            }, "pb_nalog raw"

        monkeypatch.setattr(svc, "fetch_pb_nalog_profile", fake_pb_nalog)

        _start()
        outcome = _run(captured["run_work"](123))

        assert captured_args == {"inn": "7712345678", "is_individual": False}
        assert outcome.fields["pb_nalog_data"]["mass_address_count"] == 2
        assert outcome.fields["pb_nalog_raw"] == "pb_nalog raw"
        assert "pb_nalog" in outcome.fields["checked_sources"]

    def test_uses_is_individual_true_for_individual_entrepreneurs(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": None,
            "ogrn": "123456789012345",  # 15-digit ОГРНИП -> individual_entrepreneur
            "inn": "771234567890",
            "registration_date": None,
        }
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        captured_args = {}

        async def fake_pb_nalog(inn, is_individual):
            captured_args["is_individual"] = is_individual
            return {
                "checked": True,
                "found": False,
                "mass_address_count": 0,
                "mass_address_companies": [],
                "profile_url": None,
            }, ""

        monkeypatch.setattr(svc, "fetch_pb_nalog_profile", fake_pb_nalog)

        _start()
        _run(captured["run_work"](123))

        assert captured_args["is_individual"] is True

    def test_skips_pb_nalog_when_no_resolved_inn(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        called = {"pb_nalog": False}

        async def fail_pb_nalog(inn, is_individual):
            called["pb_nalog"] = True

        monkeypatch.setattr(svc, "fetch_pb_nalog_profile", fail_pb_nalog)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called["pb_nalog"] is False
        assert outcome.fields["pb_nalog_data"]["checked"] is False

    def test_mass_address_flag_feeds_into_the_overall_risk_level(
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

        async def fake_pb_nalog(inn, is_individual):
            return {
                "checked": True,
                "found": True,
                "mass_address_count": 50,
                "mass_address_companies": [],
                "profile_url": None,
            }, "raw"

        monkeypatch.setattr(svc, "fetch_pb_nalog_profile", fake_pb_nalog)

        _start()
        outcome = _run(captured["run_work"](123))

        assert any(f["code"] == "mass_registration_address" for f in outcome.fields["flags"])
        assert outcome.fields["risk_level"] == "medium"


class TestRunWorkFedsfm:
    def test_checks_fedsfm_by_resolved_director_name(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {
            "director_name": "Иванов Иван Иванович",
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
                        "matched": False,
                        "requires_manual_review": False,
                        "matches": [],
                    },
                    "",
                )
            ),
        )

        captured_name = {}

        async def fake_fedsfm(name):
            captured_name["name"] = name
            return {
                "checked": True,
                "matched": False,
                "requires_manual_review": False,
                "matches": [],
            }, "fedsfm raw"

        monkeypatch.setattr(svc, "check_terrorist_list", fake_fedsfm)

        _start()
        outcome = _run(captured["run_work"](123))

        assert captured_name["name"] == "Иванов Иван Иванович"
        assert outcome.fields["fedsfm_raw"] == "fedsfm raw"
        assert "fedsfm" in outcome.fields["checked_sources"]

    def test_skips_fedsfm_when_no_director_name(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        called = {"fedsfm": False}

        async def fail_fedsfm(name):
            called["fedsfm"] = True

        monkeypatch.setattr(svc, "check_terrorist_list", fail_fedsfm)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called["fedsfm"] is False
        assert outcome.fields["fedsfm_result"]["checked"] is False
        assert "fedsfm" not in outcome.fields["checked_sources"]

    def test_fedsfm_match_flag_feeds_into_the_overall_risk_level(
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
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))
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

        async def fake_fedsfm(name):
            return {
                "checked": True,
                "matched": True,
                "requires_manual_review": True,
                "matches": [{"full_name": "Иванов Иван Иванович"}],
            }, "raw"

        monkeypatch.setattr(svc, "check_terrorist_list", fake_fedsfm)

        _start()
        outcome = _run(captured["run_work"](123))

        assert any(f["code"] == "fedsfm_possible_match" for f in outcome.fields["flags"])
        assert outcome.fields["risk_level"] == "medium"


class TestRunWorkWebsite:
    """`website` is stored as-is (trimmed) and displayed - never fetched or analyzed by
    this feature itself (see ru_business_check_service.py's module docstring)."""

    def test_website_is_stripped_and_stored_on_the_outcome(self, monkeypatch, fake_db, captured):
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

        _start(website=" example.ru ")
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["website"] == "example.ru"

    def test_no_website_is_stored_as_none(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        _start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields["website"] is None

    def test_website_never_appears_in_checked_or_pending_sources(
        self, monkeypatch, fake_db, captured
    ):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        _start(website="example.ru")
        outcome = _run(captured["run_work"](123))

        assert "website" not in outcome.fields["checked_sources"]
        assert "website" not in outcome.fields["pending_sources"]


class TestRunWorkZakupkiRnp:
    def test_fetches_rnp_entries_by_resolved_inn(self, monkeypatch, fake_db, captured):
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

        async def fake_rnp(inn):
            captured_inn["inn"] = inn
            return [], "rnp raw"

        monkeypatch.setattr(svc, "fetch_rnp_entries", fake_rnp)

        _start()
        outcome = _run(captured["run_work"](123))

        assert captured_inn["inn"] == "7712345678"
        assert outcome.fields["rnp_raw"] == "rnp raw"
        assert outcome.fields["rnp_data"] == {"checked": True, "entries": []}
        assert "zakupki_rnp" in outcome.fields["checked_sources"]

    def test_skips_rnp_when_no_resolved_inn(self, monkeypatch, fake_db, captured):
        monkeypatch.setattr(
            svc, "find_recent_completed_search_by_query", _async(lambda db, query, max_age: None)
        )
        egrul_data = {"director_name": None, "ogrn": None, "inn": None, "registration_date": None}
        monkeypatch.setattr(svc, "fetch_egrul_extract", _async(lambda query: (egrul_data, "raw")))

        called = {"rnp": False}

        async def fail_rnp(inn):
            called["rnp"] = True

        monkeypatch.setattr(svc, "fetch_rnp_entries", fail_rnp)

        _start()
        outcome = _run(captured["run_work"](123))

        assert called["rnp"] is False
        assert outcome.fields["rnp_data"] == {"checked": False, "entries": []}
        assert "zakupki_rnp" not in outcome.fields["checked_sources"]

    def test_a_confirmed_rnp_match_forces_high_risk(self, monkeypatch, fake_db, captured):
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

        async def fake_rnp(inn):
            return [
                {
                    "registry_number": "1",
                    "law": "44-ФЗ",
                    "name": "ООО Ромашка",
                    "inn": inn,
                    "status": "Размещено",
                }
            ], "raw"

        monkeypatch.setattr(svc, "fetch_rnp_entries", fake_rnp)

        _start()
        outcome = _run(captured["run_work"](123))

        assert any(f["code"] == "rnp_confirmed" for f in outcome.fields["flags"])
        assert outcome.fields["risk_level"] == "high"
