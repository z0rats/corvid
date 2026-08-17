"""arbitration_service's pure parsing helpers, tested against synthetic JSON matching the
response shape described in the module docstring - unverified against a live capture, so
this fixture is the thing to update first if a real capture shows a different structure."""

from app.features.ru_business_check.service.arbitration_service import (
    _coerce_amount,
    parse_response,
)

INN = "7712345678"

SAMPLE_RESPONSE = {
    "Success": True,
    "Result": {
        "TotalCount": 2,
        "Items": [
            {
                "CaseId": "abc-123",
                "CaseNumber": "А40-11111/2023",
                "DateRegister": "2023-01-15T00:00:00",
                "Status": "Рассмотрение",
                "Court": "АС города Москвы",
                "Sum": 50000,
                "Sides": [
                    {"Name": "ООО «Нитка»", "Inn": INN, "Role": "Ответчик"},
                    {"Name": "Истец ООО", "Inn": "9998887776", "Role": "Истец"},
                ],
            },
            {
                "CaseId": "def-456",
                "CaseNumber": "А40-22222/2022",
                "DateRegister": "2022-05-10T00:00:00",
                "Status": "Завершено",
                "Court": "АС города Москвы",
                "Sum": "1 500 000,00",
                "Sides": [
                    {"Name": "ООО «Нитка»", "Inn": INN, "Role": "Ответчик"},
                ],
            },
        ],
    },
}


class TestParseResponse:
    def test_extracts_both_cases(self):
        cases = parse_response(SAMPLE_RESPONSE, INN)
        assert len(cases) == 2

    def test_determines_role_from_the_side_matching_our_inn(self):
        cases = parse_response(SAMPLE_RESPONSE, INN)
        assert all(c["role"] == "defendant" for c in cases)

    def test_falls_back_to_other_role_for_unrecognized_text(self):
        response = {
            "Result": {
                "Items": [
                    {
                        "CaseId": "x",
                        "CaseNumber": "A1",
                        "Sides": [{"Inn": INN, "Role": "Непонятная роль"}],
                    }
                ]
            }
        }
        cases = parse_response(response, INN)
        assert cases[0]["role"] == "other"

    def test_builds_case_url_from_case_id(self):
        cases = parse_response(SAMPLE_RESPONSE, INN)
        assert cases[0]["case_url"] == "https://kad.arbitr.ru/Card/abc-123"

    def test_skips_items_without_a_case_number(self):
        response = {"Result": {"Items": [{"CaseId": "x", "Sides": []}]}}
        assert parse_response(response, INN) == []

    def test_empty_items_returns_empty_list(self):
        assert parse_response({"Result": {"Items": []}}, INN) == []
        assert parse_response({}, INN) == []


class TestCoerceAmount:
    def test_passes_through_numeric_types(self):
        assert _coerce_amount(50000) == 50000.0
        assert _coerce_amount(50000.5) == 50000.5

    def test_parses_a_formatted_russian_string(self):
        assert _coerce_amount("1 500 000,00") == 1500000.0

    def test_returns_none_for_missing_or_unparseable_values(self):
        assert _coerce_amount(None) is None
        assert _coerce_amount("не число") is None
