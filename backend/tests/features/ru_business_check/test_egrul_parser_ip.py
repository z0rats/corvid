"""egrul_service.parse_pdf_text against real ИП (individual entrepreneur) выписки -
`fixtures/sample_egrul_extract_ip_active.txt` and `..._ip_terminated.txt` (name/ИНН/ОГРНИП
anonymized, structure and labels untouched). Both captured live against egrul.nalog.ru
while closing a known gap: ЕГРИП uses a materially different label set from ЕГРЮЛ, and
was entirely unverified until this capture - a query for one previously came back with
almost every field empty.

The terminated record exists specifically to verify `registry_status`: an active record
has no status section in the PDF at all (confirmed by its total absence in both this
active fixture and the ЕГРЮЛ one in test_egrul_parser.py), so a terminated one was needed
to see what a non-empty status actually looks like.
"""

from pathlib import Path

from app.features.ru_business_check.service.egrul_service import parse_pdf_text

FIXTURES_DIR = Path(__file__).parent / "fixtures"
ACTIVE_IP_TEXT = (FIXTURES_DIR / "sample_egrul_extract_ip_active.txt").read_text(encoding="utf-8")
TERMINATED_IP_TEXT = (FIXTURES_DIR / "sample_egrul_extract_ip_terminated.txt").read_text(
    encoding="utf-8"
)


class TestActiveIndividualEntrepreneur:
    def test_full_name_falls_back_to_the_entrepreneur_s_own_name(self):
        # ЕГРИП has no separate legal-entity name field at all - unlike ЕГРЮЛ, where
        # _FULL_NAME_LABEL matches directly.
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["full_name"] == "ИП ИВАНОВ ИВАН ИВАНОВИЧ"

    def test_director_name_resolves_to_the_entrepreneur_themselves(self):
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["director_name"] == "ИВАНОВ ИВАН ИВАНОВИЧ"
        assert result["director_position"] is None  # no "Должность" concept for an ИП

    def test_extracts_ogrnip_and_personal_inn(self):
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["ogrn"] == "319000000000001"  # 15-digit ОГРНИП, not a 13-digit ОГРН
        assert result["inn"] == "771234567890"

    def test_extracts_registration_date(self):
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["registration_date"] == "2019-08-05"

    def test_fields_that_do_not_exist_for_an_ip_stay_none_not_fabricated(self):
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["kpp"] is None  # individuals have no КПП
        assert result["capital"] is None  # no уставный капитал concept
        assert result["address"] is None  # only the tax office's address is in the PDF
        assert result["founders"] == []  # a sole proprietor has no учредители

    def test_active_record_has_no_status(self):
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["registry_status"] is None

    def test_extracts_okved(self):
        result = parse_pdf_text(ACTIVE_IP_TEXT)

        assert result["okved_main"].startswith("47.91")
        assert len(result["okved_additional"]) == 3


class TestTerminatedIndividualEntrepreneur:
    def test_registry_status_captures_the_termination_reason(self):
        result = parse_pdf_text(TERMINATED_IP_TEXT)

        assert result["registry_status"] == (
            "Индивидуальный предприниматель прекратил деятельность в связи с "
            "принятием им соответствующего решения"
        )

    def test_core_fields_still_extract_for_a_terminated_record(self):
        result = parse_pdf_text(TERMINATED_IP_TEXT)

        assert result["full_name"] == "ИП ИВАНОВ ИВАН ИВАНОВИЧ"
        assert result["ogrn"] == "304000000000002"
        assert result["registration_date"] == "2004-08-23"
