"""egrul_service.parse_pdf_text, tested against `fixtures/sample_egrul_extract.txt` - the
pdfplumber-extracted text of a real ЕГРЮЛ выписка PDF (company name/ИНН/ОГРН/director
anonymized, structure and labels untouched), captured live against egrul.nalog.ru while
debugging a real user-reported timeout. This replaces an earlier version of this test
file that was written against a *guessed* layout before that capture - the real PDF
turned out to be a numbered table ("N label value", value wrapping onto following
unnumbered lines), not the simple "Label: value" shape originally assumed.
"""

from pathlib import Path

from app.features.ru_business_check.service.egrul_service import (
    _extract_rows,
    _match_label,
    _row_value,
    parse_pdf_text,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_egrul_extract.txt"
SAMPLE_EXTRACT_TEXT = FIXTURE_PATH.read_text(encoding="utf-8")


class TestExtractRows:
    def test_splits_into_one_block_per_row_number(self):
        rows = _extract_rows(SAMPLE_EXTRACT_TEXT)

        assert rows[1].startswith("Полное наименование на русском языке")
        assert rows[9] == "ОГРН 1147700000001"
        assert rows[10] == "Дата регистрации 12.12.2014"

    def test_a_bare_sub_item_counter_line_is_not_mistaken_for_a_row_start(self):
        # Regression: a standalone "1" line (OKVED/records sub-item counter) with no
        # trailing text on the same line must never merge into the *next* real row via
        # a \s+ that crosses the newline - see _ROW_START_RE's own comment.
        rows = _extract_rows(SAMPLE_EXTRACT_TEXT)

        assert 1 in rows
        assert rows[1].startswith("Полное наименование")
        assert "Причина внесения записи" not in rows[1]

    def test_page_header_and_footer_noise_is_stripped(self):
        rows = _extract_rows(SAMPLE_EXTRACT_TEXT)

        for content in rows.values():
            assert "Выписка из ЕГРЮЛ" not in content
            assert "Страница" not in content


class TestRowValue:
    def test_finds_the_first_matching_row(self):
        rows = _extract_rows(SAMPLE_EXTRACT_TEXT)

        assert _row_value(rows, "ОГРН") == "1147700000001"

    def test_collapses_a_wrapped_multiline_value_to_single_spaces(self):
        rows = _extract_rows(SAMPLE_EXTRACT_TEXT)

        value = _row_value(rows, "Полное наименование на русском языке")
        assert "\n" not in value
        assert 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "НИТКА"' == value

    def test_returns_none_when_label_not_present(self):
        rows = _extract_rows(SAMPLE_EXTRACT_TEXT)

        assert _row_value(rows, "Совершенно другая метка") is None


class TestMatchLabel:
    def test_a_label_that_is_a_prefix_of_a_different_field_does_not_match(self):
        # Regression: "ОГРН" is a plain string-prefix of "ОГРНИП" (a *different* field,
        # ИП's own registration number) - str.startswith alone would wrongly strip
        # "ОГРН" off "ОГРНИП 319..." and return "ИП 319..." as if it were the value.
        assert _match_label("ОГРНИП 319000000000001", "ОГРН") is None

    def test_the_label_followed_by_a_space_does_match(self):
        assert _match_label("ОГРН 1147700000001", "ОГРН") == "1147700000001"

    def test_the_bare_label_with_nothing_after_it_returns_none(self):
        assert _match_label("ОГРН", "ОГРН") is None


class TestParsePdfText:
    def test_extracts_core_registry_fields(self):
        result = parse_pdf_text(SAMPLE_EXTRACT_TEXT)

        assert result["full_name"] == 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "НИТКА"'
        assert result["ogrn"] == "1147700000001"
        assert result["inn"] == "7712345678"
        assert result["kpp"] == "771201001"
        assert result["registration_date"] == "2014-12-12"
        assert result["address"] == "123456, Г.МОСКВА, УЛ. ПРИМЕРНАЯ, Д. 1"

    def test_extracts_director_as_the_first_name_block(self):
        result = parse_pdf_text(SAMPLE_EXTRACT_TEXT)

        assert result["director_name"] == "ИВАНОВ ИВАН ИВАНОВИЧ"
        assert result["director_position"] == "ГЕНЕРАЛЬНЫЙ ДИРЕКТОР"

    def test_extracts_founders_after_the_director_block_with_their_share(self):
        result = parse_pdf_text(SAMPLE_EXTRACT_TEXT)

        assert result["founders"] == [{"name": "ИВАНОВ ИВАН ИВАНОВИЧ", "share": "100%"}]

    def test_first_okved_hit_is_main_the_rest_are_additional(self):
        result = parse_pdf_text(SAMPLE_EXTRACT_TEXT)

        assert result["okved_main"].startswith("56.10")
        assert len(result["okved_additional"]) == 12
        assert result["okved_additional"][0].startswith("47.11")
        assert result["okved_main"] not in result["okved_additional"]

    def test_extracts_capital_not_a_founders_nominal_share_value(self):
        result = parse_pdf_text(SAMPLE_EXTRACT_TEXT)

        # "Размер (в рублях)" (capital) vs "Номинальная стоимость доли (в рублях)"
        # (a founder's own share value) share a suffix - must not be confused.
        assert result["capital"] == "10000"

    def test_missing_fields_are_none_not_raising(self):
        result = parse_pdf_text("Некий нераспознанный текст без меток")

        assert result["full_name"] is None
        assert result["director_name"] is None
        assert result["founders"] == []
        assert result["okved_additional"] == []

    def test_unparseable_date_leaves_registration_date_none(self):
        text = SAMPLE_EXTRACT_TEXT.replace(
            "10 Дата регистрации 12.12.2014", "10 Дата регистрации не дата"
        )
        result = parse_pdf_text(text)

        assert result["registration_date"] is None

    def test_registration_date_ignores_a_section_header_that_bled_into_the_same_row(self):
        # Regression: when a row's value has no wrapped continuation of its own, the
        # *next* unnumbered section-header line (there's no generic way to strip section
        # headers - see _extract_shape's docstring) gets folded into the row's captured
        # span. Confirmed live on a real ИП record: row 9's raw content was literally
        # "Дата регистрации 05.08.2019 Сведения о регистрирующем органе по месту
        # жительства индивидуального предпринимателя" - only the date shape should be
        # extracted, not the trailing garbage.
        text = SAMPLE_EXTRACT_TEXT.replace(
            "10 Дата регистрации 12.12.2014",
            "10 Дата регистрации 12.12.2014\nСведения о некоем разделе,\nвклинившемся в значение",
        )
        result = parse_pdf_text(text)

        assert result["registration_date"] == "2014-12-12"
