"""report_service.build_sections/generate_ru_business_check_report - focused mostly on the
per-source `href` construction, since that's the part with real logic (which fields
already carry a specific per-request URL vs. which fall back to a source's homepage).
"""

import datetime

from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch
from app.features.ru_business_check.service.report_service import (
    build_sections,
    generate_ru_business_check_report,
)


def _search(**overrides) -> RuBusinessCheckSearch:
    defaults = dict(
        id=1,
        query="7712345678",
        resolved_inn="7712345678",
        entity_type="legal_entity",
        risk_level="low",
        completed_at=datetime.datetime(2026, 8, 14, 12, 0, tzinfo=datetime.UTC),
        egrul_data=None,
        disqualification_result=None,
        arbitration_data=None,
        fedresurs_data=None,
        pb_nalog_data=None,
        fedsfm_result=None,
        rnp_data=None,
        website=None,
        flags=[],
        checked_sources=["egrul"],
        pending_sources=[],
        candidates=[],
    )
    defaults.update(overrides)
    return RuBusinessCheckSearch(**defaults)


def _section(sections, title):
    return next(s for s in sections if s.title == title)


def _row(section, label):
    return next(r for r in section.rows if r.label == label)


class TestSummarySection:
    def test_always_present_even_with_no_other_data(self):
        sections = build_sections(_search())
        assert sections[0].title == "Итог"

    def test_includes_flags_and_source_coverage(self):
        search = _search(
            flags=[{"code": "x", "severity": "hard", "title": "T", "detail": "D"}],
            checked_sources=["egrul", "arbitration"],
            pending_sources=["fssp"],
        )
        section = build_sections(search)[0]
        assert any("Флаг (жёсткий)" in r.label and "T: D" in r.value for r in section.rows)
        assert any("Проверенные источники" == r.label for r in section.rows)
        assert any("Не проверено" == r.label for r in section.rows)


class TestEgrulSection:
    def test_links_to_the_general_egrul_homepage_no_stable_per_record_url(self):
        search = _search(egrul_data={"full_name": "ООО Ромашка", "inn": "7712345678"})
        section = _section(build_sections(search), "ЕГРЮЛ/ЕГРИП")
        source_row = _row(section, "Источник")
        assert source_row.href == "https://egrul.nalog.ru"


class TestArbitrationSection:
    def test_links_each_case_to_its_own_case_url_not_the_kad_arbitr_homepage(self):
        search = _search(
            arbitration_data={
                "checked": True,
                "cases": [
                    {
                        "case_number": "A40-1/2023",
                        "role": "defendant",
                        "status": "Рассмотрение",
                        "claim_amount": 150000,
                        "case_url": "https://kad.arbitr.ru/Card/abc-123",
                    }
                ],
            }
        )
        section = _section(build_sections(search), "Арбитражные дела")
        row = _row(section, "Дело 1")
        assert row.href == "https://kad.arbitr.ru/Card/abc-123"
        assert "150" in row.value  # amount formatted

    def test_no_cases_is_a_clean_result_row_not_an_empty_section(self):
        search = _search(arbitration_data={"checked": True, "cases": []})
        section = _section(build_sections(search), "Арбитражные дела")
        assert _row(section, "Результат").value == "Дел не найдено"


class TestFedresursSection:
    def test_links_to_the_specific_profile_url_when_found(self):
        search = _search(
            fedresurs_data={
                "checked": True,
                "found": True,
                "status_text": "Действующее",
                "is_active_bankruptcy": False,
                "profile_url": "https://fedresurs.ru/company/abc",
            }
        )
        section = _section(build_sections(search), "Банкротство (Федресурс)")
        assert _row(section, "Источник").href == "https://fedresurs.ru/company/abc"

    def test_falls_back_to_the_homepage_when_not_found(self):
        search = _search(
            fedresurs_data={
                "checked": True,
                "found": False,
                "status_text": None,
                "is_active_bankruptcy": False,
                "profile_url": None,
            }
        )
        section = _section(build_sections(search), "Банкротство (Федресурс)")
        assert _row(section, "Источник").href == "https://fedresurs.ru"


class TestDisqualificationSection:
    def test_manual_check_link_spells_out_the_director_name_and_targets_the_search_page(self):
        search = _search(
            egrul_data={"director_name": "Иванов Иван Иванович"},
            disqualification_result={
                "checked": True,
                "matched": False,
                "requires_manual_review": False,
                "matches": [],
            },
        )
        section = _section(build_sections(search), "Реестр дисквалифицированных лиц (РДЛ)")
        row = _row(section, "Проверить вручную")
        assert row.href == "https://service.nalog.ru/disqualified.do"
        assert "Иванов Иван Иванович" in row.value

    def test_manual_check_link_still_present_with_no_director_name(self):
        search = _search(
            egrul_data={},
            disqualification_result={
                "checked": True,
                "matched": False,
                "requires_manual_review": False,
                "matches": [],
            },
        )
        section = _section(build_sections(search), "Реестр дисквалифицированных лиц (РДЛ)")
        row = _row(section, "Проверить вручную")
        assert row.href == "https://service.nalog.ru/disqualified.do"


class TestFedsfmSection:
    def test_manual_check_link_spells_out_the_director_name_and_targets_the_search_page(self):
        search = _search(
            egrul_data={"director_name": "Иванов Иван Иванович"},
            fedsfm_result={
                "checked": True,
                "matched": False,
                "requires_manual_review": False,
                "matches": [],
            },
        )
        section = _section(build_sections(search), "Перечень терроризм/ОМУ (ФедСФМ)")
        row = _row(section, "Проверить вручную")
        assert row.href == "https://fedsfm.ru/documents/terr-list"
        assert "Иванов Иван Иванович" in row.value


class TestRnpSection:
    def test_links_each_entry_to_its_own_detail_url(self):
        search = _search(
            rnp_data={
                "checked": True,
                "entries": [
                    {
                        "registry_number": "26008859",
                        "law": "44-ФЗ",
                        "name": 'ООО "СОКОЛСТРОЙ"',
                        "included_date": "13.08.2026",
                        "detail_url": "https://zakupki.gov.ru/epz/dishonestsupplier/view/info.html?reestrNumber=26008859&law=FZ44",
                    }
                ],
            }
        )
        section = _section(build_sections(search), "Реестр недобросовестных поставщиков (РНП)")
        row = _row(section, "Запись №26008859")
        assert row.href == (
            "https://zakupki.gov.ru/epz/dishonestsupplier/view/info.html"
            "?reestrNumber=26008859&law=FZ44"
        )

    def test_adds_a_repeat_search_link_using_the_resolved_inn(self):
        search = _search(resolved_inn="7712345678", rnp_data={"checked": True, "entries": []})
        section = _section(build_sections(search), "Реестр недобросовестных поставщиков (РНП)")
        row = _row(section, "Проверить вручную")
        assert row.href.startswith(
            "https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html?"
        )
        assert "searchString=7712345678" in row.href

    def test_no_repeat_search_link_without_a_resolved_inn(self):
        search = _search(resolved_inn=None, rnp_data={"checked": True, "entries": []})
        section = _section(build_sections(search), "Реестр недобросовестных поставщиков (РНП)")
        assert not any(r.label == "Проверить вручную" for r in section.rows)


class TestWebsiteSection:
    def test_links_directly_to_the_site_itself(self):
        search = _search(website="example.ru")
        section = _section(build_sections(search), "Домен компании")
        row = _row(section, "Сайт")
        assert row.value == "example.ru"
        assert row.href == "https://example.ru"

    def test_no_website_produces_no_section(self):
        sections = build_sections(_search(website=None))
        assert "Домен компании" not in [s.title for s in sections]


class TestSectionOmission:
    def test_a_source_that_was_never_checked_produces_no_section(self):
        sections = build_sections(_search())
        titles = [s.title for s in sections]
        assert "Арбитражные дела" not in titles
        assert "Банкротство (Федресурс)" not in titles
        assert "Домен компании" not in titles


class TestGenerateReport:
    def test_html_format_produces_utf8_bytes_with_the_query_and_a_source_link(self):
        search = _search(
            egrul_data={"full_name": "ООО Ромашка", "inn": "7712345678"},
        )
        content, media_type, filename = generate_ru_business_check_report(search, "html")

        assert media_type == "text/html"
        html = content.decode("utf-8")
        assert "7712345678" in html
        assert 'href="https://egrul.nalog.ru"' in html
        assert filename == "ru-business-check-1-7712345678.html"

    def test_pdf_format_produces_pdf_bytes(self):
        content, media_type, _filename = generate_ru_business_check_report(_search(), "pdf")

        assert media_type == "application/pdf"
        assert content.startswith(b"%PDF")

    def test_filename_sanitizes_the_query(self):
        search = _search(query='ООО "Ромашка & Ко"/тест')
        _content, _media_type, filename = generate_ru_business_check_report(search, "html")

        assert filename.startswith("ru-business-check-1-")
        assert " " not in filename
        assert "/" not in filename
