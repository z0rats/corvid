"""flag_engine.evaluate is pure - no network/DB - so these exercise it directly against
synthetic ЕГРЮЛ/РДЛ results rather than mocking anything."""

import datetime

from app.features.ru_business_check.service import flag_engine

NO_DISQUALIFICATION = {
    "checked": True,
    "matched": False,
    "requires_manual_review": False,
    "matches": [],
}


def _egrul(registration_date: str | None = None) -> dict:
    return {"registration_date": registration_date}


class TestFreshRegistrationFlag:
    def test_no_flag_when_no_registration_date(self):
        flags, risk = flag_engine.evaluate(
            _egrul(None), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"

    def test_soft_flag_when_registered_recently(self):
        recent = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        flags, risk = flag_engine.evaluate(
            _egrul(recent), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "fresh_registration"
        assert flags[0]["severity"] == "soft"
        assert risk == "medium"

    def test_no_flag_when_registered_before_threshold(self):
        old = (datetime.date.today() - datetime.timedelta(days=1000)).isoformat()
        flags, risk = flag_engine.evaluate(
            _egrul(old), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"

    def test_no_flag_on_unparseable_date(self):
        flags, risk = flag_engine.evaluate(
            _egrul("not-a-date"), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"


class TestDisqualificationFlags:
    def test_no_match_produces_no_flag(self):
        flags, risk = flag_engine.evaluate(
            _egrul(), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"

    def test_match_requiring_manual_review_is_soft_not_hard(self):
        disqualification = {
            "checked": True,
            "matched": True,
            "requires_manual_review": True,
            "matches": [{"full_name": "Иванов Иван Иванович"}],
        }
        flags, risk = flag_engine.evaluate(
            _egrul(), disqualification, fresh_registration_threshold_days=365
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "disqualified_possible_match"
        assert flags[0]["severity"] == "soft"
        assert risk == "medium"

    def test_confirmed_match_is_a_hard_flag_and_forces_high_risk(self):
        disqualification = {
            "checked": True,
            "matched": True,
            "requires_manual_review": False,
            "matches": [{"full_name": "Иванов Иван Иванович"}],
        }
        recent = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        flags, risk = flag_engine.evaluate(
            _egrul(recent), disqualification, fresh_registration_threshold_days=365
        )
        severities = {f["severity"] for f in flags}
        assert "hard" in severities
        assert risk == "high"


class TestRiskLevelAggregation:
    def test_zero_flags_is_low(self):
        _, risk = flag_engine.evaluate(
            _egrul(), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert risk == "low"

    def test_any_hard_flag_is_high_regardless_of_soft_count(self):
        disqualification = {
            "checked": True,
            "matched": True,
            "requires_manual_review": False,
            "matches": [],
        }
        _, risk = flag_engine.evaluate(
            _egrul(), disqualification, fresh_registration_threshold_days=365
        )
        assert risk == "high"


def _evaluate_arbitration(cases, **overrides):
    kwargs = dict(
        fresh_registration_threshold_days=365,
        small_claim_amount_threshold=100_000,
        large_claim_amount_threshold=1_000_000,
        multiple_claims_defendant_threshold=3,
    )
    kwargs.update(overrides)
    return flag_engine.evaluate(_egrul(), NO_DISQUALIFICATION, cases, **kwargs)


class TestArbitrationFlags:
    def test_no_cases_produces_no_flag(self):
        flags, risk = _evaluate_arbitration([])
        assert flags == []
        assert risk == "low"

    def test_arbitration_cases_none_is_distinct_from_empty_list_but_both_produce_no_flag(self):
        flags, _ = flag_engine.evaluate(
            _egrul(), NO_DISQUALIFICATION, None, fresh_registration_threshold_days=365
        )
        assert flags == []

    def test_plaintiff_only_cases_produce_no_flag(self):
        cases = [{"role": "plaintiff", "status": "Завершено", "claim_amount": 50}]
        flags, risk = _evaluate_arbitration(cases)
        assert flags == []
        assert risk == "low"

    def test_single_small_resolved_defendant_case_is_soft(self):
        cases = [
            {
                "case_number": "A1",
                "role": "defendant",
                "status": "Завершено",
                "claim_amount": 10_000,
            }
        ]
        flags, risk = _evaluate_arbitration(cases)
        assert len(flags) == 1
        assert flags[0]["code"] == "single_small_resolved_claim"
        assert flags[0]["severity"] == "soft"
        assert risk == "medium"

    def test_single_unresolved_small_defendant_case_produces_no_flag(self):
        cases = [
            {
                "case_number": "A1",
                "role": "defendant",
                "status": "Рассмотрение",
                "claim_amount": 10_000,
            }
        ]
        flags, risk = _evaluate_arbitration(cases)
        assert flags == []
        assert risk == "low"

    def test_single_large_claim_triggers_significant_flag_even_though_only_one_case(self):
        cases = [
            {
                "case_number": "A1",
                "role": "defendant",
                "status": "Рассмотрение",
                "claim_amount": 5_000_000,
            }
        ]
        flags, risk = _evaluate_arbitration(cases)
        codes = [f["code"] for f in flags]
        assert "significant_or_multiple_claims_as_defendant" in codes
        assert risk == "medium"

    def test_three_or_more_defendant_cases_trigger_multiple_claims_flag_regardless_of_amount(self):
        cases = [
            {
                "case_number": f"A{i}",
                "role": "defendant",
                "status": "Рассмотрение",
                "claim_amount": None,
            }
            for i in range(3)
        ]
        flags, risk = _evaluate_arbitration(cases)
        codes = [f["code"] for f in flags]
        assert "significant_or_multiple_claims_as_defendant" in codes
        assert "single_small_resolved_claim" not in codes

    def test_missing_claim_amount_is_treated_as_small_not_large(self):
        cases = [
            {"case_number": "A1", "role": "defendant", "status": "Завершено", "claim_amount": None}
        ]
        flags, risk = _evaluate_arbitration(cases)
        codes = [f["code"] for f in flags]
        assert "single_small_resolved_claim" in codes
        assert "significant_or_multiple_claims_as_defendant" not in codes

    def test_thresholds_are_respected_when_customized(self):
        cases = [
            {
                "case_number": "A1",
                "role": "defendant",
                "status": "Рассмотрение",
                "claim_amount": 200_000,
            }
        ]
        flags, _ = _evaluate_arbitration(cases, large_claim_amount_threshold=150_000)
        assert any(f["code"] == "significant_or_multiple_claims_as_defendant" for f in flags)


NOT_BANKRUPT = {
    "checked": True,
    "found": True,
    "status_text": "Действующее",
    "is_active_bankruptcy": False,
    "profile_url": None,
}

ACTIVE_BANKRUPTCY = {
    "checked": True,
    "found": True,
    "status_text": "Юридическое лицо признано несостоятельным (банкротом)",
    "is_active_bankruptcy": True,
    "profile_url": "https://fedresurs.ru/company/abc",
}


class TestFedresursFlags:
    def test_active_bankruptcy_is_a_hard_flag_and_forces_high_risk(self):
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=ACTIVE_BANKRUPTCY,
            fresh_registration_threshold_days=365,
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "active_bankruptcy"
        assert flags[0]["severity"] == "hard"
        assert risk == "high"

    def test_clean_status_produces_no_flag(self):
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=NOT_BANKRUPT,
            fresh_registration_threshold_days=365,
        )
        assert flags == []
        assert risk == "low"

    def test_not_found_produces_no_flag(self):
        not_found = {
            "checked": True,
            "found": False,
            "status_text": None,
            "is_active_bankruptcy": False,
            "profile_url": None,
        }
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=not_found,
            fresh_registration_threshold_days=365,
        )
        assert flags == []
        assert risk == "low"

    def test_fedresurs_result_none_is_distinct_from_checked_but_produces_no_flag_either_way(self):
        flags, _ = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=None,
            fresh_registration_threshold_days=365,
        )
        assert flags == []


def _pb_nalog(mass_address_count=0):
    return {
        "checked": True,
        "found": True,
        "mass_address_count": mass_address_count,
        "mass_address_companies": [],
        "profile_url": None,
    }


class TestPbNalogFlags:
    def test_below_threshold_mass_address_count_produces_no_flag(self):
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            pb_nalog_result=_pb_nalog(mass_address_count=3),
            fresh_registration_threshold_days=365,
            mass_address_threshold=10,
        )
        assert flags == []
        assert risk == "low"

    def test_at_threshold_mass_address_count_is_a_soft_flag(self):
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            pb_nalog_result=_pb_nalog(mass_address_count=10),
            fresh_registration_threshold_days=365,
            mass_address_threshold=10,
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "mass_registration_address"
        assert flags[0]["severity"] == "soft"
        assert risk == "medium"

    def test_pb_nalog_result_none_produces_no_flag(self):
        flags, _ = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            pb_nalog_result=None,
            fresh_registration_threshold_days=365,
        )
        assert flags == []

    def test_not_found_result_produces_no_flag(self):
        not_found = {
            "checked": True,
            "found": False,
            "mass_address_count": 0,
            "mass_address_companies": [],
            "profile_url": None,
        }
        flags, _ = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            pb_nalog_result=not_found,
            fresh_registration_threshold_days=365,
        )
        assert flags == []


NO_FEDSFM_MATCH = {
    "checked": True,
    "matched": False,
    "requires_manual_review": False,
    "matches": [],
}


class TestFedsfmFlags:
    def test_no_match_produces_no_flag(self):
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedsfm_result=NO_FEDSFM_MATCH,
            fresh_registration_threshold_days=365,
        )
        assert flags == []
        assert risk == "low"

    def test_match_is_soft_not_hard_and_never_auto_confirmed(self):
        fedsfm_result = {
            "checked": True,
            "matched": True,
            "requires_manual_review": True,
            "matches": [{"full_name": "Иванов Иван Иванович"}],
        }
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedsfm_result=fedsfm_result,
            fresh_registration_threshold_days=365,
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "fedsfm_possible_match"
        assert flags[0]["severity"] == "soft"
        assert risk == "medium"

    def test_fedsfm_result_none_produces_no_flag(self):
        flags, _ = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedsfm_result=None,
            fresh_registration_threshold_days=365,
        )
        assert flags == []


class TestZakupkiRnpFlags:
    def test_no_entries_produces_no_flag(self):
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            rnp_entries=[],
            fresh_registration_threshold_days=365,
        )
        assert flags == []
        assert risk == "low"

    def test_rnp_entries_none_produces_no_flag(self):
        flags, _ = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            rnp_entries=None,
            fresh_registration_threshold_days=365,
        )
        assert flags == []

    def test_a_match_is_a_hard_flag_and_forces_high_risk(self):
        entries = [
            {
                "registry_number": "26008859",
                "law": "44-ФЗ",
                "name": 'ООО "СОКОЛСТРОЙ"',
                "inn": "4813028017",
                "status": "Размещено",
            }
        ]
        flags, risk = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            rnp_entries=entries,
            fresh_registration_threshold_days=365,
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "rnp_confirmed"
        assert flags[0]["severity"] == "hard"
        assert "СОКОЛСТРОЙ" in flags[0]["detail"]
        assert "44-ФЗ" in flags[0]["detail"]
        assert risk == "high"

    def test_multiple_entries_are_counted_and_deduplicated_by_law(self):
        entries = [
            {"registry_number": "1", "law": "44-ФЗ", "name": "ООО Ромашка", "inn": "1"},
            {"registry_number": "2", "law": "44-ФЗ", "name": "ООО Ромашка", "inn": "1"},
        ]
        flags, _ = flag_engine.evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            rnp_entries=entries,
            fresh_registration_threshold_days=365,
        )
        assert len(flags) == 1
        assert flags[0]["detail"].count("44-ФЗ") == 1
        assert "Найдено 2" in flags[0]["detail"]
