"""flag_engine.evaluate is pure - no network/DB - so these exercise it directly against
synthetic ЕГРЮЛ/РДЛ results rather than mocking anything."""

import dataclasses
import datetime

from app.features.ru_business_check.service import flag_engine

NO_DISQUALIFICATION = {
    "checked": True,
    "matched": False,
    "requires_manual_review": False,
    "matches": [],
}


_THRESHOLD_NAMES = {f.name for f in dataclasses.fields(flag_engine.Thresholds)}
_POSITIONAL_SOURCES = ("arbitration_cases", "fedresurs", "pb_nalog", "fedsfm", "rnp_entries")


def _evaluate(egrul, disqualification, *positional, checked_sources=None, **kwargs):
    """`flag_engine.evaluate` with each source/threshold as a keyword: `<source>_result=` or
    the positional order (arbitration cases, Федресурс, pb.nalog, ФедСФМ, РНП) for sources,
    any `Thresholds` field name for thresholds."""
    thresholds = {k: kwargs.pop(k) for k in list(kwargs) if k in _THRESHOLD_NAMES}
    sources = dict(zip(_POSITIONAL_SOURCES, positional, strict=False))
    sources.update({k.removesuffix("_result"): v for k, v in kwargs.items()})
    return flag_engine.evaluate(
        flag_engine.SourceResults(egrul=egrul, disqualification=disqualification, **sources),
        flag_engine.Thresholds(**thresholds),
        checked_sources,
    )


def _egrul(registration_date: str | None = None) -> dict:
    return {"registration_date": registration_date}


class TestFreshRegistrationFlag:
    def test_no_flag_when_no_registration_date(self):
        flags, risk = _evaluate(
            _egrul(None), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"

    def test_soft_flag_when_registered_recently(self):
        recent = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        flags, risk = _evaluate(
            _egrul(recent), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert len(flags) == 1
        assert flags[0]["code"] == "fresh_registration"
        assert flags[0]["severity"] == "soft"
        assert risk == "medium"

    def test_no_flag_when_registered_before_threshold(self):
        old = (datetime.date.today() - datetime.timedelta(days=1000)).isoformat()
        flags, risk = _evaluate(
            _egrul(old), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"

    def test_no_flag_on_unparseable_date(self):
        flags, risk = _evaluate(
            _egrul("not-a-date"), NO_DISQUALIFICATION, fresh_registration_threshold_days=365
        )
        assert flags == []
        assert risk == "low"


class TestDisqualificationFlags:
    def test_no_match_produces_no_flag(self):
        flags, risk = _evaluate(
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
        flags, risk = _evaluate(_egrul(), disqualification, fresh_registration_threshold_days=365)
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
        flags, risk = _evaluate(
            _egrul(recent), disqualification, fresh_registration_threshold_days=365
        )
        severities = {f["severity"] for f in flags}
        assert "hard" in severities
        assert risk == "high"


class TestRiskLevelAggregation:
    def test_zero_flags_is_low(self):
        _, risk = _evaluate(_egrul(), NO_DISQUALIFICATION, fresh_registration_threshold_days=365)
        assert risk == "low"

    def test_any_hard_flag_is_high_regardless_of_soft_count(self):
        disqualification = {
            "checked": True,
            "matched": True,
            "requires_manual_review": False,
            "matches": [],
        }
        _, risk = _evaluate(_egrul(), disqualification, fresh_registration_threshold_days=365)
        assert risk == "high"


def _evaluate_arbitration(cases, **overrides):
    kwargs = dict(
        fresh_registration_threshold_days=365,
        small_claim_amount_threshold=100_000,
        large_claim_amount_threshold=1_000_000,
        multiple_claims_defendant_threshold=3,
    )
    kwargs.update(overrides)
    return _evaluate(_egrul(), NO_DISQUALIFICATION, cases, **kwargs)


class TestArbitrationFlags:
    def test_no_cases_produces_no_flag(self):
        flags, risk = _evaluate_arbitration([])
        assert flags == []
        assert risk == "low"

    def test_arbitration_cases_none_is_distinct_from_empty_list_but_both_produce_no_flag(self):
        flags, _ = _evaluate(
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
        flags, risk = _evaluate(
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
        flags, risk = _evaluate(
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
        flags, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=not_found,
            fresh_registration_threshold_days=365,
        )
        assert flags == []
        assert risk == "low"

    def test_fedresurs_result_none_is_distinct_from_checked_but_produces_no_flag_either_way(self):
        flags, _ = _evaluate(
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
        flags, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            pb_nalog_result=_pb_nalog(mass_address_count=3),
            fresh_registration_threshold_days=365,
            mass_address_threshold=10,
        )
        assert flags == []
        assert risk == "low"

    def test_at_threshold_mass_address_count_is_a_soft_flag(self):
        flags, risk = _evaluate(
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
        flags, _ = _evaluate(
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
        flags, _ = _evaluate(
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
        flags, risk = _evaluate(
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
        flags, risk = _evaluate(
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
        flags, _ = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedsfm_result=None,
            fresh_registration_threshold_days=365,
        )
        assert flags == []


class TestZakupkiRnpFlags:
    def test_no_entries_produces_no_flag(self):
        flags, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            rnp_entries=[],
            fresh_registration_threshold_days=365,
        )
        assert flags == []
        assert risk == "low"

    def test_rnp_entries_none_produces_no_flag(self):
        flags, _ = _evaluate(
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
        flags, risk = _evaluate(
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
        flags, _ = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            rnp_entries=entries,
            fresh_registration_threshold_days=365,
        )
        assert len(flags) == 1
        assert flags[0]["detail"].count("44-ФЗ") == 1
        assert "Найдено 2" in flags[0]["detail"]


def _fedresurs(**overrides):
    result = {
        "checked": True,
        "found": True,
        "status_text": "Действующее",
        "is_active_bankruptcy": False,
        "status_recognized": True,
        "profile_url": None,
        "signals": [],
    }
    result.update(overrides)
    return result


ALL_REQUIRED = ["egrul", "fedresurs", "zakupki_rnp"]


class TestFedresursSignalFlags:
    def test_unrecognized_status_is_a_soft_flag_not_silence(self):
        flags, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=_fedresurs(status_text="Ликвидировано", status_recognized=False),
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert [f["code"] for f in flags] == ["fedresurs_status_unrecognized"]
        assert flags[0]["severity"] == "soft"
        assert "Ликвидировано" in flags[0]["detail"]
        assert risk == "medium"

    def test_each_signal_code_becomes_one_soft_flag_with_its_count(self):
        signals = [
            {"code": "creditor_bankruptcy_intent", "date": "2026-09-01"},
            {"code": "creditor_bankruptcy_intent", "date": "2026-09-10"},
            {"code": "reorganization", "date": "2026-03-01"},
        ]
        flags, _ = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=_fedresurs(signals=signals),
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert [f["code"] for f in flags] == ["creditor_bankruptcy_intent", "reorganization"]
        assert all(f["severity"] == "soft" for f in flags)
        assert "Сообщений на Федресурсе: 2" in flags[0]["detail"]

    def test_several_fedresurs_signals_alone_never_escalate_to_high(self):
        signals = [
            {"code": code, "date": "2026-09-01"}
            for code in (
                "creditor_bankruptcy_intent",
                "debtor_bankruptcy_intent",
                "liquidation_decision",
                "unreliable_information",
                "reorganization",
            )
        ]
        flags, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=_fedresurs(signals=signals),
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert len(flags) == 5
        assert risk == "medium"


class TestSoftFlagsCountOncePerSource:
    def test_three_independent_sources_with_soft_flags_escalate_to_high(self):
        flags, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=_fedresurs(signals=[{"code": "reorganization", "date": "2026-03-01"}]),
            pb_nalog_result={"mass_address_count": 50},
            fedsfm_result={"matched": True, "matches": [{"full_name": "X"}]},
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert {f["code"] for f in flags} == {
            "reorganization",
            "mass_registration_address",
            "fedsfm_possible_match",
        }
        assert risk == "high"

    def test_two_sources_are_not_enough(self):
        _, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=_fedresurs(signals=[{"code": "reorganization", "date": "2026-03-01"}]),
            pb_nalog_result={"mass_address_count": 50},
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert risk == "medium"

    def test_one_source_emitting_two_flags_counts_once(self):
        cases = [
            {"case_number": f"A{i}", "role": "defendant", "status": "Рассмотрение"}
            for i in range(3)
        ]
        cases[0]["claim_amount"] = 5_000_000
        _, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            arbitration_cases=cases,
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert risk == "medium"


class TestIncompleteVerdict:
    def test_no_flags_but_a_required_source_missing_is_incomplete_not_low(self):
        for missing in ALL_REQUIRED:
            checked = [s for s in ALL_REQUIRED if s != missing]
            _, risk = _evaluate(
                _egrul(),
                NO_DISQUALIFICATION,
                fresh_registration_threshold_days=365,
                checked_sources=checked,
            )
            assert risk == "incomplete", missing

    def test_soft_flags_with_a_required_source_missing_are_incomplete_not_medium(self):
        _, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            pb_nalog_result={"mass_address_count": 50},
            fresh_registration_threshold_days=365,
            checked_sources=["egrul", "fedresurs"],
        )
        assert risk == "incomplete"

    def test_a_hard_flag_stays_high_even_when_other_required_sources_failed(self):
        _, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fedresurs_result=ACTIVE_BANKRUPTCY,
            fresh_registration_threshold_days=365,
            checked_sources=["egrul", "fedresurs"],
        )
        assert risk == "high"

    def test_failed_soft_only_sources_do_not_make_the_verdict_incomplete(self):
        # арбитраж/РДЛ/ФедСФМ/pb.nalog never raise a hard flag, so their failure is
        # surfaced via pending_sources but doesn't invalidate the verdict.
        _, risk = _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert risk == "low"

    def test_every_hard_flag_capable_source_is_required(self):
        # Structural: a source that can emit a hard flag must be in REQUIRED_SOURCES,
        # otherwise its failure could produce a clean-looking verdict.
        import inspect

        from app.features.ru_business_check.config.ru_business_check_config import (
            REQUIRED_SOURCES,
        )

        hard_sources = {
            "fedresurs": flag_engine._fedresurs_flags,
            "zakupki_rnp": flag_engine._zakupki_rnp_flags,
        }
        for source, fn in hard_sources.items():
            assert '"hard"' in inspect.getsource(fn)
            assert source in REQUIRED_SOURCES


def _gir_bo(*years, checked=True):
    return {"checked": checked, "found": True, "has_reports": True, "years": list(years)}


def _year(year, **lines):
    base = {
        "year": year,
        "revenue": 100.0,
        "assets": 100.0,
        "equity": 50.0,
        "current_assets": 80.0,
        "current_liabilities": 40.0,
    }
    base.update(lines)
    return base


def _eval_gir_bo(result, **kwargs):
    return _evaluate(
        _egrul(),
        NO_DISQUALIFICATION,
        gir_bo_result=result,
        fresh_registration_threshold_days=365,
        checked_sources=ALL_REQUIRED,
        **kwargs,
    )


class TestGirBoFlags:
    def test_healthy_statements_raise_nothing(self):
        flags, risk = _eval_gir_bo(_gir_bo(_year(2025), _year(2024)))
        assert flags == []
        assert risk == "low"

    def test_low_equity_ratio_including_negative_equity(self):
        flags, _ = _eval_gir_bo(_gir_bo(_year(2025, equity=-20.0)))
        assert [f["code"] for f in flags] == ["low_equity_ratio"]
        assert "отрицательный" in flags[0]["detail"]

    def test_low_current_liquidity(self):
        flags, _ = _eval_gir_bo(_gir_bo(_year(2025, current_assets=30.0, current_liabilities=60.0)))
        assert [f["code"] for f in flags] == ["low_current_liquidity"]

    def test_revenue_drop_between_consecutive_years(self):
        flags, _ = _eval_gir_bo(_gir_bo(_year(2025, revenue=40.0), _year(2024, revenue=100.0)))
        assert [f["code"] for f in flags] == ["revenue_drop"]
        assert "60%" in flags[0]["detail"]

    def test_a_gap_in_filings_is_not_a_year_over_year_drop(self):
        flags, _ = _eval_gir_bo(_gir_bo(_year(2025, revenue=10.0), _year(2023, revenue=100.0)))
        assert flags == []

    def test_missing_lines_are_not_assessed_rather_than_failed(self):
        flags, _ = _eval_gir_bo(
            _gir_bo(_year(2025, equity=None, current_assets=None, revenue=None), _year(2024))
        )
        assert flags == []

    def test_zero_denominators_are_skipped(self):
        flags, _ = _eval_gir_bo(_gir_bo(_year(2025, assets=0.0, current_liabilities=0.0)))
        assert flags == []

    def test_thresholds_are_respected(self):
        result = _gir_bo(_year(2025, equity=20.0))  # ratio 0.2
        assert _eval_gir_bo(result)[0] == []
        flags, _ = _eval_gir_bo(result, equity_ratio_threshold=0.3)
        assert [f["code"] for f in flags] == ["low_equity_ratio"]

    def test_unchecked_or_empty_result_raises_nothing(self):
        assert _eval_gir_bo({"checked": False, "years": []})[0] == []
        assert _eval_gir_bo({"checked": True, "found": False, "years": []})[0] == []

    def test_all_three_financial_flags_count_as_one_source(self):
        flags, risk = _eval_gir_bo(
            _gir_bo(
                _year(2025, equity=1.0, current_assets=10.0, revenue=10.0),
                _year(2024, revenue=100.0),
            )
        )
        assert len(flags) == 3
        assert risk == "medium"


def _dump(*, confirmed=False, company_records=(), director_records=()):
    return {
        "checked": True,
        "dump_date": "2026-09-20",
        "director_confirmed": confirmed,
        "director_records": list(director_records),
        "company_records": list(company_records),
    }


def _dump_record(**overrides):
    record = {
        "record_number": "100000000001",
        "full_name": "ИВАНОВ ИВАН ИВАНОВИЧ",
        "active": True,
        "same_company": True,
        "start_date": "2025-11-28",
        "end_date": "2027-11-27",
    }
    record.update(overrides)
    return record


ONLINE_NAME_ONLY_HIT = {
    "checked": True,
    "matched": True,
    "requires_manual_review": True,
    "matches": [{"full_name": "ИВАНОВ ИВАН ИВАНОВИЧ"}],
}


class TestDisqualifiedDumpFlags:
    def _evaluate(self, dump, online=NO_DISQUALIFICATION):
        return _evaluate(
            _egrul(),
            online,
            disqualified_dump_result=dump,
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )

    def test_name_and_company_inn_match_in_force_is_a_hard_flag(self):
        record = _dump_record()
        flags, risk = self._evaluate(
            _dump(confirmed=True, director_records=[record], company_records=[record])
        )
        assert [f["code"] for f in flags] == ["disqualified_confirmed"]
        assert flags[0]["severity"] == "hard"
        assert "100000000001" in flags[0]["detail"]
        assert risk == "high"

    def test_the_hard_flag_supersedes_the_online_name_only_soft_flag(self):
        record = _dump_record()
        flags, _ = self._evaluate(
            _dump(confirmed=True, director_records=[record], company_records=[record]),
            online=ONLINE_NAME_ONLY_HIT,
        )
        assert [f["code"] for f in flags] == ["disqualified_confirmed"]

    def test_without_a_dump_confirmation_the_online_soft_flag_stays(self):
        flags, risk = self._evaluate(
            _dump(director_records=[_dump_record(same_company=False)]), online=ONLINE_NAME_ONLY_HIT
        )
        assert [f["code"] for f in flags] == ["disqualified_possible_match"]
        assert risk == "medium"

    def test_an_officer_of_the_company_in_force_is_a_soft_signal(self):
        flags, risk = self._evaluate(_dump(company_records=[_dump_record(full_name="ПЕТРОВ П П")]))
        assert [f["code"] for f in flags] == ["company_disqualified_officer"]
        assert flags[0]["severity"] == "soft"
        assert "ПЕТРОВ" not in flags[0]["detail"]  # third-party names stay in the panel
        assert risk == "medium"

    def test_expired_company_records_are_a_soft_signal_with_their_dates(self):
        flags, risk = self._evaluate(
            _dump(
                company_records=[
                    _dump_record(active=False, start_date="2020-01-01", end_date="2022-01-01")
                ]
            )
        )
        assert [f["code"] for f in flags] == ["company_disqualified_officer"]
        assert flags[0]["title"].startswith("У компании были")
        assert "2020-01-01 — 2022-01-01 (истекла)" in flags[0]["detail"]
        assert risk == "medium"

    def test_an_active_company_record_says_is_and_lists_its_dates(self):
        flags, _ = self._evaluate(_dump(company_records=[_dump_record()]))
        assert flags[0]["title"].startswith("У компании есть")
        assert "2025-11-28 — 2027-11-27 (действует)" in flags[0]["detail"]

    def test_unchecked_dump_raises_nothing(self):
        flags, _ = self._evaluate({"checked": False})
        assert flags == []


def _cbr(*records, checked=True):
    return {"checked": checked, "as_of": "2026-09-28", "records": list(records)}


class TestCbrWarningFlags:
    def _evaluate(self, cbr):
        return _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            cbr_warning_result=cbr,
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )

    def test_a_listed_company_gets_a_soft_flag_worded_as_the_regulators_statement(self):
        flags, risk = self._evaluate(
            _cbr({"sign": 'Признаки "финансовой пирамиды"', "listed_at": "2024-05-01"})
        )
        assert [f["code"] for f in flags] == ["cbr_warning_list"]
        assert flags[0]["severity"] == "soft"
        assert "Банк России сообщает" in flags[0]["detail"]
        assert "не решение суда" in flags[0]["detail"]
        assert "в списке с 2024-05-01" in flags[0]["detail"]
        assert risk == "medium"

    def test_a_clone_entry_raises_nothing_against_the_impersonated_inn_owner(self):
        flags, risk = self._evaluate(_cbr({"sign": "Признаки пирамиды", "is_clone": True}))
        assert flags == []
        assert risk == "low"

    def test_a_closed_entry_still_counts(self):
        flags, _ = self._evaluate(_cbr({"sign": "Признаки пирамиды", "closed": True}))
        assert [f["code"] for f in flags] == ["cbr_warning_list"]

    def test_no_records_or_unchecked_raises_nothing(self):
        assert self._evaluate(_cbr())[0] == []
        assert self._evaluate(_cbr({"sign": "x"}, checked=False))[0] == []


class TestOfacSdnFlags:
    def _evaluate(self, ofac):
        return _evaluate(
            _egrul(),
            NO_DISQUALIFICATION,
            ofac_sdn_result=ofac,
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )

    def test_an_exact_inn_match_is_a_hard_flag_worded_as_a_us_list_status(self):
        record = {
            "ent_num": 1,
            "name": "OOO TRANSOIL",
            "kind": "entity",
            "programs": "RUSSIA-EO14024",
        }
        flags, risk = self._evaluate({"checked": True, "records": [record]})
        assert [f["code"] for f in flags] == ["ofac_sdn_listed"]
        assert flags[0]["severity"] == "hard"
        assert "OOO TRANSOIL" in flags[0]["detail"]
        assert "не запрет по российскому праву" in flags[0]["detail"]
        assert risk == "high"

    def test_no_match_or_unchecked_raises_nothing(self):
        assert self._evaluate({"checked": True, "records": []})[0] == []
        assert self._evaluate({"checked": False, "records": [{"name": "x"}]})[0] == []


class TestThresholdsFromSettings:
    def test_reads_every_field_from_the_settings_row_by_name(self):
        from app.core.settings.ru_business_check.models.ru_business_check_settings_models import (
            RuBusinessCheckSettings,
        )

        row = RuBusinessCheckSettings(
            **{f.name: 7 for f in dataclasses.fields(flag_engine.Thresholds)}
        )
        assert flag_engine.Thresholds.from_settings(row) == flag_engine.Thresholds(
            **{f.name: 7 for f in dataclasses.fields(flag_engine.Thresholds)}
        )

    def test_every_threshold_is_a_settings_column(self):
        from app.core.settings.ru_business_check.models.ru_business_check_settings_models import (
            RuBusinessCheckSettings,
        )

        columns = set(RuBusinessCheckSettings.__table__.columns.keys())
        assert _THRESHOLD_NAMES <= columns


class TestDumpIsItsOwnSource:
    def test_online_registry_dump_and_a_third_source_make_three_independent_soft_sources(self):
        record = _dump_record(same_company=True, active=False, full_name="ПЕТРОВ П П")
        _, risk = _evaluate(
            _egrul(),
            ONLINE_NAME_ONLY_HIT,
            disqualified_dump_result=_dump(company_records=[record]),
            pb_nalog_result={"mass_address_count": 50},
            fresh_registration_threshold_days=365,
            checked_sources=ALL_REQUIRED,
        )
        assert risk == "high"
