"""Structural gate: every source parser in this feature must turn a drifted response
into its own error class, never into an empty ("checked, nothing found") result.

If you add a source client, add its drifted-payload case to `DRIFT_CASES` - the
`AVAILABLE_SOURCES` completeness test fails until you do, which is the point: a new
scraper must decide, up front, what schema drift looks like for it."""

import pytest

from app.features.ru_business_check.config.ru_business_check_config import AVAILABLE_SOURCES
from app.features.ru_business_check.service import (
    arbitration_service,
    cbr_warning_service,
    disqualified_dump_service,
    disqualified_persons_service,
    egrul_service,
    fedresurs_service,
    fedsfm_service,
    gir_bo_service,
    msp_service,
    ofac_sdn_service,
    pb_nalog_service,
    zakupki_rnp_service,
)
from app.features.ru_business_check.service.source_contract import (
    require_dict,
    require_fields,
    require_list_field,
)

INN = "7707083893"

# source key -> (callable taking the drifted payload, expected error class)
DRIFT_CASES = {
    "arbitration": (
        lambda p: arbitration_service.parse_response(p, INN),
        arbitration_service.ArbitrationError,
    ),
    "egrul": (egrul_service._select_row, egrul_service.EgrulError),
    "fedresurs (search row)": (
        lambda p: fedresurs_service.pick_search_row(p, INN),
        fedresurs_service.FedresursError,
    ),
    "fedresurs": (
        lambda p: fedresurs_service.parse_publications(p, "guid"),
        fedresurs_service.FedresursError,
    ),
    "cbr_warning": (
        lambda p: cbr_warning_service.parse_list(p),
        cbr_warning_service.CbrWarningError,
    ),
    "disqualified_dump": (
        disqualified_dump_service.parse_dump,
        disqualified_dump_service.DisqualifiedDumpError,
    ),
    "disqualified_persons": (
        disqualified_persons_service.parse_results,
        disqualified_persons_service.DisqualifiedPersonsError,
    ),
    "fedsfm": (fedsfm_service._parse_matches, fedsfm_service.FedsfmError),
    "gir_bo": (lambda p: gir_bo_service.pick_organization(p, INN), gir_bo_service.GirBoError),
    "msp": (lambda p: msp_service.parse_msp(p, INN), msp_service.MspError),
    "ofac_sdn": (lambda p: ofac_sdn_service.parse_sdn(p), ofac_sdn_service.OfacSdnError),
    "pb_nalog": (
        lambda p: pb_nalog_service._pick_matching_row(p, INN, is_individual=False),
        pb_nalog_service.PbNalogError,
    ),
    "zakupki_rnp": (
        lambda p: zakupki_rnp_service.parse_rss_entries(p),
        zakupki_rnp_service.ZakupkiRnpError,
    ),
}

DRIFTED_PAYLOADS = {
    "arbitration": {"Result": {}},
    "egrul": {"rows": [{"t": "token-only"}]},
    "fedresurs": {"pageData": None, "found": 0},
    "fedresurs (search row)": {"pageData": [{"inn": INN, "guid": "g"}], "found": 1},
    "cbr_warning": '{"RC": null}',
    "disqualified_dump": "G1,G2\nx,y\n",
    "disqualified_persons": "<html>captcha</html>",
    "fedsfm": {"IsError": False, "recordsTotal": 3},
    "gir_bo": {"content": None},
    "msp": {"rowCount": 0},
    "ofac_sdn": "1,ONLY,THREE\n",
    "pb_nalog": {"ul": {}, "ip": {"data": []}},
    "zakupki_rnp": "<html>stub</html>",
}


def test_every_available_source_has_a_drift_case():
    missing = set(AVAILABLE_SOURCES) - set(DRIFT_CASES)
    assert not missing, f"add a schema-drift case for: {sorted(missing)}"


@pytest.mark.parametrize("source", sorted(DRIFT_CASES))
def test_drifted_payload_raises_the_sources_own_error(source):
    parse, error = DRIFT_CASES[source]
    with pytest.raises(error, match="схема (ответа|выгрузки) изменилась"):
        parse(DRIFTED_PAYLOADS[source])


class TestHelpers:
    def test_require_dict_rejects_non_objects(self):
        for bad in (None, [], "x", 1):
            with pytest.raises(ValueError, match="не JSON-объект"):
                require_dict(bad, error=ValueError, label="L")

    def test_require_list_field_accepts_an_empty_list_but_not_a_missing_or_non_list(self):
        assert require_list_field({"a": []}, "a", error=ValueError, label="L") == []
        for bad in ({}, {"a": None}, {"a": "x"}, None):
            with pytest.raises(ValueError):
                require_list_field(bad, "a", error=ValueError, label="L")

    def test_require_fields_treats_a_null_value_as_present_but_an_absent_key_as_drift(self):
        assert require_fields({"a": None}, ("a",), error=ValueError, label="L") == {"a": None}
        with pytest.raises(ValueError, match="нет поля «b»"):
            require_fields({"a": 1}, ("a", "b"), error=ValueError, label="L")


class TestCanaryOutcomePolicy:
    """The canary's skip/fail split, pinned: skipping a real drift would hide exactly what the
    canary exists to catch."""

    @pytest.fixture
    def classify(self):
        from tests.canary.policy import UNREACHABLE

        return UNREACHABLE

    @pytest.mark.parametrize(
        "message",
        [
            "fedresurs.ru недоступен: timeout",
            "kad.arbitr.ru временно ограничил доступ (защита от частых запросов)",
            "pb.nalog.ru запросил капчу — попробуйте позже",
            "zakupki.gov.ru вернул ошибку: HTTP 451",
            "bo.nalog.gov.ru вернул ошибку: HTTP 503",
        ],
    )
    def test_unreachable_is_skipped(self, classify, message):
        assert classify.search(message)

    @pytest.mark.parametrize(
        "message",
        [
            "Федресурс: схема ответа изменилась — нет поля «status»",
            "fedresurs.ru: выдача поиска усечена или без счётчика",
            "Ничего не найдено в ЕГРЮЛ/ЕГРИП по этому запросу",
            "bo.nalog.gov.ru вернул ошибку: HTTP 404",
            # A JSON endpoint answering HTML may be an anti-bot page - or a changed API; the
            # weekly canary surfaces it for a human to tell.
            "fedresurs.ru вернул не-JSON (возможна антибот-страница)",
            "список ЦБ: схема ответа изменилась — ответ не JSON",
        ],
    )
    def test_drift_and_unexpected_answers_fail(self, classify, message):
        assert not classify.search(message)
