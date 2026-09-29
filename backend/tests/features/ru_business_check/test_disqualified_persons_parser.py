"""disqualified_persons_service's parsing helpers. The JSON shape (`disqualified-proc.json`,
what the live site returns) was captured 2026-09-28; the values here are synthetic. The HTML
table fixtures are the legacy fallback shape, synthetic and never captured live."""

import asyncio

import httpx
import pytest

from app.features.ru_business_check.service.disqualified_persons_service import (
    DisqualifiedPersonsError,
    _discover_search_field,
    check_disqualified,
    parse_results,
    parse_results_html,
    parse_results_json,
)

SEARCH_PAGE_HTML = """
<html><body>
<form method="get" action="/disqualified.do">
    <input type="hidden" name="csrf" value="abc123">
    <input type="text" name="fio" placeholder="ФИО">
    <button type="submit">Найти</button>
</form>
</body></html>
"""

RESULTS_TABLE_HTML = """
<html><body>
<table>
<tr>
<th>№ п/п</th><th>Номер записи РДЛ</th><th>Дисквалифицированное лицо</th>
<th>Организация, должность</th><th>Статья КоАП РФ</th>
<th>Наименование органа</th><th>Судья</th><th>Сведения о дисквалификации</th>
</tr>
<tr>
<td>1</td><td>РДЛ-001</td><td>Иванов Иван Иванович</td>
<td>ООО Ромашка, Генеральный директор</td><td>ст. 14.25</td>
<td>ФНС России</td><td>Петров П.П.</td><td>дисквалифицирован на 1 год</td>
</tr>
</table>
</body></html>
"""

NO_RESULTS_HTML = "<html><body><p>Совпадений не найдено</p></body></html>"


class TestDiscoverSearchField:
    def test_finds_hidden_fields_and_first_text_input(self):
        method, action, fields = _discover_search_field(SEARCH_PAGE_HTML)

        assert method == "get"
        assert action.endswith("/disqualified.do")
        assert fields["csrf"] == "abc123"
        assert fields["__query_field__"] == "fio"

    def test_raises_when_no_form_present(self):
        with pytest.raises(DisqualifiedPersonsError):
            _discover_search_field("<html><body>no form here</body></html>")

    def test_raises_when_no_text_input_present(self):
        html = (
            '<html><body><form action="/x"><input type="hidden" name="a" '
            'value="1"></form></body></html>'
        )
        with pytest.raises(DisqualifiedPersonsError):
            _discover_search_field(html)


class TestParseResultsHtml:
    def test_extracts_a_matching_row(self):
        rows = parse_results_html(RESULTS_TABLE_HTML)

        assert len(rows) == 1
        row = rows[0]
        assert row["full_name"] == "Иванов Иван Иванович"
        assert row["record_number"] == "РДЛ-001"
        assert row["organization"] == "ООО Ромашка"
        assert row["position"] == "Генеральный директор"
        assert row["article"] == "ст. 14.25"
        assert row["issuing_authority"] == "ФНС России"
        assert row["judge"] == "Петров П.П."
        assert row["details"] == "дисквалифицирован на 1 год"

    def test_no_table_returns_empty_list(self):
        assert parse_results_html(NO_RESULTS_HTML) == []

    def test_header_only_table_returns_empty_list(self):
        html = "<table><tr><th>№ п/п</th><th>ФИО</th></tr></table>"
        assert parse_results_html(html) == []


# Row shape captured live from service.nalog.ru/disqualified-proc.json (values synthetic).
JSON_ROW = {
    "ROW_NUM": 1,
    "ДатаФорм": "25.09.2026 22:23:53",
    "КолЗап": 8215,
    "НомЗап": "264800064492",
    "ФИО": "ИВАНОВ ИВАН ИВАНОВИЧ",
    "ДатаРожд": "23.03.1966 00:00:00",
    "МестоРожд": "Г. ТУЛА",
    "НаимОрг": 'ООО "РОМАШКА"',
    "Должность": "ГЕНЕРАЛЬНЫЙ ДИРЕКТОР",
    "КвалификацияТекст": "Ч.5 СТ. 14.25 КОАП РФ",
    "НаимОргПрот": "УФНС РОССИИ ПО ТУЛЬСКОЙ ОБЛАСТИ",
    "ФИОСуд": "ПЕТРОВА П. П.",
    "ДолжностьСуд": "СУДЬЯ",
    "ДисквСрок": "1 г.",
    "ДатаНачДискв": "01.02.2026 00:00:00",
    "ДатаКонДискв": "01.02.2027 00:00:00",
    "row_cnt": 1,
}
EMPTY_JSON = {"data": [], "rowCount": 0, "page": 1, "pageSize": 25}


class TestParseResultsJson:
    def test_extracts_a_match_from_the_live_row_shape(self):
        (match,) = parse_results_json({"data": [JSON_ROW], "rowCount": 1})
        assert match["full_name"] == "ИВАНОВ ИВАН ИВАНОВИЧ"
        assert match["record_number"] == "264800064492"
        assert match["birth_date"] == "23.03.1966"
        assert match["organization"] == 'ООО "РОМАШКА"'
        assert match["position"] == "ГЕНЕРАЛЬНЫЙ ДИРЕКТОР"
        assert match["article"] == "Ч.5 СТ. 14.25 КОАП РФ"
        assert match["issuing_authority"] == "УФНС РОССИИ ПО ТУЛЬСКОЙ ОБЛАСТИ"
        assert match["judge"] == "ПЕТРОВА П. П."
        assert match["details"] == "срок: 1 г. с 01.02.2026 по 01.02.2027"

    def test_empty_data_is_the_no_match_answer(self):
        assert parse_results_json(EMPTY_JSON) == []

    def test_a_row_without_a_name_is_skipped(self):
        assert parse_results_json({"data": [{**JSON_ROW, "ФИО": ""}]}) == []

    @pytest.mark.parametrize(
        "bad", [{}, {"data": None}, {"data": "x"}, {"data": [{"НомЗап": "1"}]}, {"data": ["x"]}]
    )
    def test_drift_raises(self, bad):
        with pytest.raises(DisqualifiedPersonsError, match="схема ответа изменилась"):
            parse_results_json(bad)


class TestParseResults:
    def test_json_is_parsed_first(self):
        import json

        assert len(parse_results(json.dumps({"data": [JSON_ROW]}))) == 1

    def test_an_html_table_is_still_accepted(self):
        assert len(parse_results(RESULTS_TABLE_HTML)) == 1

    def test_an_unreadable_answer_is_an_error_never_an_empty_result(self):
        # Neither JSON nor a table: the old code read this as "no matches".
        for text in (NO_RESULTS_HTML, "<html>captcha</html>", "", "not json"):
            with pytest.raises(DisqualifiedPersonsError, match="схема ответа изменилась"):
                parse_results(text)


class TestCheckDisqualifiedAgainstTheJsonEndpoint:
    def _transport(self, payload):
        def handler(request):
            if request.method == "GET":
                # The live form POSTs its query (to disqualified-proc.json).
                return httpx.Response(200, text=SEARCH_PAGE_HTML.replace("get", "post"))
            return httpx.Response(200, json=payload)

        return handler

    def test_a_match_in_the_json_answer_is_reported_for_manual_review(self, patch_httpx_transport):
        patch_httpx_transport(self._transport({"data": [JSON_ROW], "rowCount": 1}))
        result, raw = asyncio.run(check_disqualified("Иванов Иван Иванович"))
        assert result["matched"] is True
        assert result["requires_manual_review"] is True
        assert result["matches"][0]["birth_date"] == "23.03.1966"
        assert "264800064492" in raw

    def test_an_empty_json_answer_is_a_checked_no_match(self, patch_httpx_transport):
        patch_httpx_transport(self._transport(EMPTY_JSON))
        result, _ = asyncio.run(check_disqualified("Иванов Иван Иванович"))
        assert result["checked"] is True
        assert result["matched"] is False
