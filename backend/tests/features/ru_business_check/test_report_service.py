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
        extra_data=None,
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

    def test_lists_messages_with_their_own_links_and_flags_an_unrecognized_status(self):
        search = _search(
            fedresurs_data={
                "checked": True,
                "found": True,
                "status_text": "Ликвидировано",
                "status_recognized": False,
                "is_active_bankruptcy": False,
                "profile_url": "https://fedresurs.ru/company/abc",
                "publications_note": "Показана первая страница публикаций (15 из 40)",
                "messages": [
                    {
                        "date": "2026-09-20",
                        "type": "Реорганизация юридического лица",
                        "signal": "reorganization",
                        "url": "https://fedresurs.ru/sfactmessages/m1",
                    }
                ],
            }
        )
        section = _section(build_sections(search), "Банкротство (Федресурс)")
        message = _row(section, "Сообщение от 2026-09-20")
        assert message.href == "https://fedresurs.ru/sfactmessages/m1"
        assert "учтено как признак" in message.value
        assert "15 из 40" in _row(section, "Сообщения Федресурса").value
        assert any("ручная проверка" in r.value for r in section.rows)


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


class TestGirBoSection:
    def test_lists_each_year_and_links_the_register(self):
        search = _search(
            resolved_inn="5036045205",
            extra_data={
                "gir_bo": {
                    "checked": True,
                    "unit": "тыс. руб.",
                    "years": [
                        {"year": 2025, "revenue": 396350822.0, "net_profit": 4137844.0},
                    ],
                }
            },
        )
        section = _section(build_sections(search), "Бухгалтерская отчётность (ГИР БО)")
        row = _row(section, "Отчётность за 2025")
        assert "396 350 822" in row.value
        assert "капитал и резервы —" in row.value
        assert _row(section, "Источник").href == "https://bo.nalog.gov.ru/"
        assert "5036045205" in _row(section, "Источник").value

    def test_absent_organization_is_an_explained_result_row(self):
        search = _search(
            extra_data={"gir_bo": {"checked": True, "years": [], "note": "Организации нет"}}
        )
        section = _section(build_sections(search), "Бухгалтерская отчётность (ГИР БО)")
        assert _row(section, "Результат").value == "Организации нет"

    def test_unchecked_source_adds_no_section(self):
        search = _search(extra_data={"gir_bo": {"checked": False, "years": []}})
        assert all(s.title != "Бухгалтерская отчётность (ГИР БО)" for s in build_sections(search))


class TestDisqualifiedDumpSection:
    def test_confirmed_match_and_records_are_listed(self):
        record = {
            "record_number": "1",
            "full_name": "ИВАНОВ ИВАН ИВАНОВИЧ",
            "position": "РУКОВОДИТЕЛЬ",
            "start_date": "2025-01-01",
            "end_date": "2027-01-01",
            "active": True,
            "same_company": True,
        }
        search = _search(
            extra_data={
                "disqualified_dump": {
                    "checked": True,
                    "dump_date": "2026-09-20",
                    "director_confirmed": True,
                    "director_records": [record],
                    "company_records": [record],
                }
            }
        )
        section = _section(build_sections(search), "Реестр дисквалифицированных лиц (выгрузка ФНС)")
        assert "дисквалифицирован" in _row(section, "Результат").value
        entry = _row(section, "Запись №1")
        assert "действует; совпал ИНН организации" in entry.value
        assert len([r for r in section.rows if r.label.startswith("Запись")]) == 1  # deduped

    def test_no_records_is_an_explicit_result(self):
        search = _search(
            extra_data={
                "disqualified_dump": {
                    "checked": True,
                    "dump_date": "2026-09-20",
                    "director_records": [],
                    "company_records": [],
                }
            }
        )
        section = _section(build_sections(search), "Реестр дисквалифицированных лиц (выгрузка ФНС)")
        assert "нет" in _row(section, "Результат").value


class TestCbrWarningSection:
    TITLE = "Список Банка России: признаки нелегальной деятельности"

    def test_lists_the_regulators_statement_and_marks_clones_differently(self):
        search = _search(
            extra_data={
                "cbr_warning": {
                    "checked": True,
                    "as_of": "2026-09-28",
                    "records": [
                        {"cbr_id": 1, "sign": "Признаки пирамиды", "listed_at": "2025-01-01"},
                        {"cbr_id": 2, "name": "КЛОН", "is_clone": True},
                    ],
                }
            }
        )
        section = _section(build_sections(search), self.TITLE)
        assert _row(section, "Запись №1").value.startswith("ЦБ сообщает о признаках")
        assert "против владельца ИНН не сигнал" in _row(section, "Запись №2").value

    def test_empty_result_says_absence_is_not_proof(self):
        search = _search(extra_data={"cbr_warning": {"checked": True, "as_of": "x", "records": []}})
        section = _section(build_sections(search), self.TITLE)
        assert "не означает отсутствия" in _row(section, "Результат").value


class TestOfacSdnSection:
    TITLE = "Санкционный список OFAC SDN (США)"

    def test_match_is_worded_as_a_us_status_and_the_coverage_caveat_is_always_present(self):
        search = _search(
            extra_data={
                "ofac_sdn": {
                    "checked": True,
                    "as_of": "2026-09-28",
                    "records": [
                        {
                            "ent_num": 1,
                            "name": "OOO TRANSOIL",
                            "kind": "entity",
                            "programs": "RUSSIA-EO14024",
                        }
                    ],
                }
            }
        )
        section = _section(build_sections(search), self.TITLE)
        assert "не запрет по российскому праву" in _row(section, "Запись №1").value
        assert "не означает отсутствия санкций" in _row(section, "Оговорка").value

    def test_no_match_still_carries_the_caveat(self):
        search = _search(
            extra_data={"ofac_sdn": {"checked": True, "as_of": "2026-09-28", "records": []}}
        )
        section = _section(build_sections(search), self.TITLE)
        assert _row(section, "Результат").value == "Совпадений по ИНН нет"
        assert "Список ЕС не проверялся" in _row(section, "Оговорка").value


class TestIncompleteVerdict:
    def test_summary_names_the_unchecked_required_sources(self):
        search = _search(
            risk_level="incomplete",
            checked_sources=["egrul", "zakupki_rnp"],
            pending_sources=["fedresurs", "fssp"],
        )
        section = _section(build_sections(search), "Итог")
        row = _row(section, "Вердикт не выдан")
        assert "Банкротство (Федресурс)" in row.value
        assert "ЕГРЮЛ" not in row.value

    def test_no_such_row_for_a_complete_verdict(self):
        section = _section(build_sections(_search(risk_level="low")), "Итог")
        assert all(r.label != "Вердикт не выдан" for r in section.rows)


class TestCbrNotApplicable:
    def test_an_individual_gets_the_explanation_not_an_empty_match(self):
        search = _search(
            extra_data={
                "cbr_warning": {
                    "checked": True,
                    "as_of": None,
                    "records": [],
                    "not_applicable": "для ИП сверка не применяется",
                }
            }
        )
        section = _section(
            build_sections(search), "Список Банка России: признаки нелегальной деятельности"
        )
        assert [(r.label, r.value) for r in section.rows] == [
            ("Результат", "для ИП сверка не применяется")
        ]

    def test_the_summary_lists_it_as_not_applicable_rather_than_unchecked(self):
        search = _search(
            pending_sources=["fssp"],
            extra_data={"cbr_warning": {"checked": True, "not_applicable": "для ИП"}},
        )
        section = _section(build_sections(search), "Итог")
        assert _row(section, "Не применимо").value == "Список ЦБ: признаки нелегальной деятельности"
        assert "Список ЦБ" not in _row(section, "Не проверено").value
