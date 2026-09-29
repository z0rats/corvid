"""zakupki_rnp_service's pure parsing functions - `_parse_description`,
`parse_rss_entries`, `_pick_exact_matches` - exercised against a real RSS response
captured live from zakupki.gov.ru (`fixtures/sample_rnp_rss.xml`, a "СТРОЙ" substring
search, 10 entries) so a future site markup change shows up as a real parsing failure
here rather than only in production.
"""

from pathlib import Path

import pytest

from app.features.ru_business_check.service.zakupki_rnp_service import (
    ZakupkiRnpError,
    _parse_description,
    _pick_exact_matches,
    parse_rss_entries,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_RSS_XML = (FIXTURES_DIR / "sample_rnp_rss.xml").read_text(encoding="utf-8")


class TestParseDescription:
    def test_extracts_all_known_fields(self):
        description_html = (
            "<strong>Реестровый номер: </strong>26008859<br/>"
            "<strong>Относится к: </strong>44-ФЗ<br/>"
            '<strong>Наименование(ФИО) недобросовестного поставщика: </strong>ООО "СОКОЛСТРОЙ"<br/>'
            "<strong>ИНН (аналог ИНН): </strong>4813028017<br/>"
            "<strong>Включено: </strong>13.08.2026<br/>"
            "<strong>Обновлено: </strong>13.08.2026<br/>"
            "<strong>Планируемая дата исключения: </strong>14.08.2028<br/>"
            "<strong>Статус записи: </strong>Размещено<br/>"
            "<strong>Номер реестровой записи ЕРУЗ: </strong>20018347<br/>"
        )
        fields = _parse_description(description_html)
        assert fields == {
            "registry_number": "26008859",
            "law": "44-ФЗ",
            "name": 'ООО "СОКОЛСТРОЙ"',
            "inn": "4813028017",
            "included_date": "13.08.2026",
            "updated_date": "13.08.2026",
            "planned_exclusion_date": "14.08.2028",
            "status": "Размещено",
            "eruz_number": "20018347",
        }

    def test_unknown_labels_are_ignored(self):
        description_html = (
            "<strong>Параметры поиска: </strong>x<br/>"
            "<strong>ИНН (аналог ИНН): </strong>4813028017<br/>"
        )
        assert _parse_description(description_html) == {"inn": "4813028017"}

    def test_empty_description_produces_no_fields(self):
        assert _parse_description("") == {}


class TestParseRssEntries:
    def test_extracts_all_ten_entries_from_the_live_fixture(self):
        entries = parse_rss_entries(SAMPLE_RSS_XML)
        assert len(entries) == 10

    def test_first_entry_has_the_expected_fields_and_detail_url(self):
        entries = parse_rss_entries(SAMPLE_RSS_XML)
        first = entries[0]
        assert first["registry_number"] == "26008859"
        assert first["law"] == "44-ФЗ"
        assert first["inn"] == "4813028017"
        assert first["status"] == "Размещено"
        assert first["detail_url"] == (
            "https://zakupki.gov.ru/epz/dishonestsupplier/view/info.html"
            "?reestrNumber=26008859&law=FZ44"
        )

    def test_entries_without_an_inn_are_dropped(self):
        xml_text = (
            "<rss><channel><item><link>/x</link>"
            "<description>&lt;strong&gt;Реестровый номер: &lt;/strong&gt;1&lt;br/&gt;</description>"
            "</item></channel></rss>"
        )
        # Every item lacking an ИНН means the label/shape changed - that must not read as
        # "nothing in the registry".
        with pytest.raises(ZakupkiRnpError, match="схема ответа изменилась"):
            parse_rss_entries(xml_text)

    def test_an_item_without_an_inn_is_dropped_next_to_valid_ones(self):
        good = (
            "<item><link>/a</link><description>"
            "&lt;strong&gt;ИНН (аналог ИНН): &lt;/strong&gt;7707083893&lt;br/&gt;"
            "</description></item>"
        )
        bad = (
            "<item><link>/b</link><description>"
            "&lt;strong&gt;Реестровый номер: &lt;/strong&gt;1&lt;br/&gt;</description></item>"
        )
        entries = parse_rss_entries(f"<rss><channel>{good}{bad}</channel></rss>")
        assert [e["inn"] for e in entries] == ["7707083893"]

    def test_response_without_an_rss_channel_is_schema_drift(self):
        with pytest.raises(ZakupkiRnpError, match="нет RSS-канала"):
            parse_rss_entries("<html><body>Доступ ограничен</body></html>")

    def test_no_items_produces_an_empty_list(self):
        assert parse_rss_entries("<rss><channel><description /></channel></rss>") == []


class TestPickExactMatches:
    def test_filters_out_partial_substring_matches(self):
        entries = parse_rss_entries(SAMPLE_RSS_XML)
        matches = _pick_exact_matches(entries, "4813028017")
        assert len(matches) == 1
        assert matches[0]["inn"] == "4813028017"

    def test_no_exact_match_is_an_empty_list(self):
        entries = parse_rss_entries(SAMPLE_RSS_XML)
        assert _pick_exact_matches(entries, "0000000000") == []

    def test_a_company_can_have_multiple_active_entries(self):
        # "ГАРАНТ СТРОЙ" (ИНН 3200010788) appears twice in the live fixture under
        # distinct registry numbers - both must be kept, not deduplicated away.
        entries = parse_rss_entries(SAMPLE_RSS_XML)
        matches = _pick_exact_matches(entries, "3200010788")
        assert len(matches) == 2
        assert {m["registry_number"] for m in matches} == {"26008855", "26008856"}
