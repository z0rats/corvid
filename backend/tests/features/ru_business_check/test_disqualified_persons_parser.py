"""disqualified_persons_service's pure parsing helpers, tested against synthetic HTML
matching the page structure described in the module docstring - unverified against a
live capture, so these fixtures are the thing to update first if a real page differs."""

import pytest

from app.features.ru_business_check.service.disqualified_persons_service import (
    DisqualifiedPersonsError,
    _discover_search_field,
    parse_results_html,
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
