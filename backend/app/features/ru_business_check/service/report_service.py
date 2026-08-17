"""Builds an HTML/PDF export of one RU Business Check scan via the shared
`core/reports/` renderer - same pattern as `ioc_lookup`'s and `email_analyzer`'s own
`report_service.py` modules, but Russian-only (no `locale` param/`LABELS` dict-of-dicts):
this feature's UI/report text is already Russian-only, hardcoded, since the source data is
inherently Russian (see AGENTS.md).

Every row that has a specific, real request URL behind it (an arbitration case, a
Федресурс/Прозрачный бизнес profile, a РНП registry entry) links there directly rather
than to the source's general homepage, so a reader can independently re-verify the exact
record. РНП additionally gets a "repeat this search" link with the query embedded, since
zakupki.gov.ru's own search reads its query string directly (confirmed live). РДЛ/ФедСФМ
can't offer that - both search UIs are POST/JS-driven, confirmed live to not read any URL
param - so those link to the real search page itself (not the bare homepage) with the
searched name spelled out for the reader to re-enter by hand.
"""

import re
from urllib.parse import urlencode

from app.core.reports.schemas import ReportRow, ReportSection
from app.core.reports.service import EXPORT_FORMATS, generate_report
from app.features.ru_business_check.config.ru_business_check_config import SOURCE_LABELS
from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch

REPORT_TITLE = "Отчёт RU Business Check"
GENERATED_AT_LABEL = "Сформирован"

_ENTITY_TYPE_LABELS = {
    "legal_entity": "Юридическое лицо",
    "individual_entrepreneur": "Индивидуальный предприниматель",
}
_RISK_LABELS = {"low": "Низкий", "medium": "Средний", "high": "Высокий"}
_ARBITRATION_ROLE_LABELS = {"plaintiff": "Истец", "defendant": "Ответчик", "other": "Иная роль"}

# РДЛ and ФедСФМ's own search forms are both POST/JS-driven (confirmed live - neither
# reads a query string to pre-fill or auto-run a search), so unlike РНП below there's no
# URL that reproduces the exact search - only a link to the real search page itself.
_DISQUALIFIED_PERSONS_SEARCH_URL = "https://service.nalog.ru/disqualified.do"
_FEDSFM_SEARCH_URL = "https://fedsfm.ru/documents/terr-list"


def _zakupki_rnp_search_url(inn: str) -> str:
    """zakupki.gov.ru's РНП search *does* read its query string directly (confirmed live
    via a real browser - a fresh session with no prior cookie still resolves this URL
    correctly), so this reproduces the exact same server-side search this feature itself
    already ran - see `zakupki_rnp_service.py`'s `_FIXED_PARAMS`."""
    params = {
        "searchString": inn,
        "fz94": "on",
        "fz223": "on",
        "ppRf615": "on",
        "dsStatuses": "0",
        "sortBy": "UPDATE_DATE",
        "pageNumber": "1",
        "sortDirection": "false",
        "recordsPerPage": "_10",
    }
    return f"https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html?{urlencode(params)}"


def _format_amount(amount: float | None) -> str:
    if amount is None:
        return "—"
    return f"{amount:,.0f}".replace(",", " ") + " ₽"


def _summary_section(search: RuBusinessCheckSearch) -> ReportSection:
    rows = [
        ReportRow("Запрос", search.query),
        ReportRow("ИНН", search.resolved_inn or "—"),
        ReportRow("Тип", _ENTITY_TYPE_LABELS.get(search.entity_type or "", "—")),
        ReportRow("Уровень риска", _RISK_LABELS.get(search.risk_level or "", "—")),
        ReportRow(
            "Дата завершения",
            search.completed_at.strftime("%Y-%m-%d %H:%M UTC") if search.completed_at else "—",
        ),
    ]

    for flag in search.flags or []:
        severity_label = "Флаг (жёсткий)" if flag.get("severity") == "hard" else "Флаг (мягкий)"
        rows.append(ReportRow(severity_label, f"{flag.get('title')}: {flag.get('detail')}"))

    checked_labels = [SOURCE_LABELS.get(s, s) for s in (search.checked_sources or [])]
    if checked_labels:
        rows.append(ReportRow("Проверенные источники", ", ".join(checked_labels)))
    pending_labels = [SOURCE_LABELS.get(s, s) for s in (search.pending_sources or [])]
    if pending_labels:
        rows.append(ReportRow("Не проверено", ", ".join(pending_labels)))

    if search.candidates:
        for i, candidate in enumerate(search.candidates, start=1):
            rows.append(
                ReportRow(
                    f"Совпадение {i}",
                    f"{candidate.get('name') or '—'} — ИНН {candidate.get('inn') or '—'}, "
                    f"ОГРН {candidate.get('ogrn') or '—'}",
                )
            )

    return ReportSection(title="Итог", rows=rows)


def _egrul_section(egrul_data: dict) -> ReportSection:
    rows = [
        ReportRow("Полное наименование", egrul_data.get("full_name") or "—"),
        ReportRow("ОГРН", egrul_data.get("ogrn") or "—"),
        ReportRow("ИНН", egrul_data.get("inn") or "—"),
        ReportRow("КПП", egrul_data.get("kpp") or "—"),
        ReportRow("Дата регистрации", egrul_data.get("registration_date") or "—"),
        ReportRow("Адрес", egrul_data.get("address") or "—"),
        ReportRow("Статус", egrul_data.get("registry_status") or "—"),
    ]
    director_name = egrul_data.get("director_name")
    if director_name:
        position = egrul_data.get("director_position")
        rows.append(
            ReportRow("Директор", f"{director_name} ({position})" if position else director_name)
        )
    founders = egrul_data.get("founders") or []
    if founders:
        rows.append(
            ReportRow(
                "Учредители",
                "; ".join(
                    f"{f.get('name')} — {f['share']}" if f.get("share") else (f.get("name") or "")
                    for f in founders
                ),
            )
        )
    if egrul_data.get("okved_main"):
        rows.append(ReportRow("Основной ОКВЭД", egrul_data["okved_main"]))
    if egrul_data.get("okved_additional"):
        rows.append(ReportRow("Доп. ОКВЭД", "; ".join(egrul_data["okved_additional"])))
    if egrul_data.get("capital"):
        rows.append(ReportRow("Уставный капитал", egrul_data["capital"]))

    rows.append(ReportRow("Источник", "egrul.nalog.ru", href="https://egrul.nalog.ru"))
    return ReportSection(title="ЕГРЮЛ/ЕГРИП", rows=rows)


def _disqualification_section(disq: dict, director_name: str | None) -> ReportSection:
    rows: list[ReportRow] = []
    if not disq.get("matched"):
        rows.append(ReportRow("Результат", "Совпадений не найдено"))
    else:
        if disq.get("requires_manual_review"):
            rows.append(
                ReportRow(
                    "Внимание",
                    "Совпадение по ФИО без дополнительного идентификатора — "
                    "требуется ручная проверка, не считать подтверждённым фактом",
                )
            )
        for m in disq.get("matches") or []:
            rows.append(ReportRow("ФИО", m.get("full_name") or "—"))
            if m.get("record_number"):
                rows.append(ReportRow("Номер записи РДЛ", m["record_number"]))
            if m.get("organization") or m.get("position"):
                rows.append(
                    ReportRow(
                        "Организация, должность",
                        ", ".join(filter(None, [m.get("organization"), m.get("position")])),
                    )
                )
            if m.get("article"):
                rows.append(ReportRow("Статья КоАП РФ", m["article"]))
            if m.get("issuing_authority"):
                rows.append(ReportRow("Орган", m["issuing_authority"]))
            if m.get("details"):
                rows.append(ReportRow("Сведения", m["details"]))

    rows.append(
        ReportRow(
            "Проверить вручную",
            f"Открыть service.nalog.ru и ввести «{director_name}»"
            if director_name
            else "Открыть service.nalog.ru",
            href=_DISQUALIFIED_PERSONS_SEARCH_URL,
        )
    )
    return ReportSection(title="Реестр дисквалифицированных лиц (РДЛ)", rows=rows)


def _arbitration_section(cases: list[dict]) -> ReportSection:
    if not cases:
        return ReportSection(
            title="Арбитражные дела", rows=[ReportRow("Результат", "Дел не найдено")]
        )

    rows = []
    for i, case in enumerate(cases, start=1):
        role = case.get("role") or "—"
        role_label = _ARBITRATION_ROLE_LABELS.get(role, role)
        amount_label = _format_amount(case.get("claim_amount"))
        value = (
            f"{case.get('case_number') or '—'} — {role_label}, "
            f"статус: {case.get('status') or '—'}, сумма: {amount_label}"
        )
        rows.append(ReportRow(f"Дело {i}", value, href=case.get("case_url")))
    return ReportSection(title="Арбитражные дела", rows=rows)


def _fedresurs_section(fedresurs: dict) -> ReportSection:
    if not fedresurs.get("found"):
        rows = [ReportRow("Результат", "Не найдено в реестре")]
    else:
        rows = [
            ReportRow("Статус", fedresurs.get("status_text") or "—"),
            ReportRow(
                "Активное банкротство", "Да" if fedresurs.get("is_active_bankruptcy") else "Нет"
            ),
        ]
    rows.append(
        ReportRow(
            "Источник",
            fedresurs.get("profile_url") or "fedresurs.ru",
            href=fedresurs.get("profile_url") or "https://fedresurs.ru",
        )
    )
    return ReportSection(title="Банкротство (Федресурс)", rows=rows)


def _pb_nalog_section(pb_nalog: dict) -> ReportSection:
    if not pb_nalog.get("found"):
        rows = [ReportRow("Результат", "Не найдено на pb.nalog.ru")]
    else:
        rows = [ReportRow("Компаний по адресу", str(pb_nalog.get("mass_address_count") or 0))]
        for c in pb_nalog.get("mass_address_companies") or []:
            label = f"— {c.get('name')}" if c.get("name") else "—"
            rows.append(ReportRow(label, f"ИНН {c['inn']}" if c.get("inn") else "—"))
    rows.append(
        ReportRow(
            "Источник",
            pb_nalog.get("profile_url") or "pb.nalog.ru",
            href=pb_nalog.get("profile_url") or "https://pb.nalog.ru",
        )
    )
    return ReportSection(title="Прозрачный бизнес", rows=rows)


def _fedsfm_section(fedsfm: dict, director_name: str | None) -> ReportSection:
    rows: list[ReportRow] = []
    if not fedsfm.get("matched"):
        rows.append(ReportRow("Результат", "Совпадений не найдено"))
    else:
        if fedsfm.get("requires_manual_review"):
            rows.append(
                ReportRow(
                    "Внимание",
                    "Совпадение по ФИО без дополнительного идентификатора — "
                    "требуется ручная проверка, не считать подтверждённым фактом",
                )
            )
        for m in fedsfm.get("matches") or []:
            rows.append(
                ReportRow(
                    m.get("full_name") or "—",
                    ", ".join(filter(None, [m.get("terrorist_type"), m.get("status")])) or "—",
                )
            )
    rows.append(
        ReportRow(
            "Проверить вручную",
            f"Открыть fedsfm.ru и ввести «{director_name}»"
            if director_name
            else "Открыть fedsfm.ru",
            href=_FEDSFM_SEARCH_URL,
        )
    )
    return ReportSection(title="Перечень терроризм/ОМУ (ФедСФМ)", rows=rows)


def _rnp_section(rnp: dict, resolved_inn: str | None) -> ReportSection:
    entries = rnp.get("entries") or []
    if not entries:
        rows = [ReportRow("Результат", "Действующих записей не найдено")]
    else:
        rows = [
            ReportRow(
                f"Запись №{e.get('registry_number') or '—'}",
                f"{e.get('name') or '—'} — {e.get('law') or '—'}, "
                f"включено {e.get('included_date') or '—'}",
                href=e.get("detail_url"),
            )
            for e in entries
        ]
    if resolved_inn:
        rows.append(
            ReportRow(
                "Проверить вручную",
                "Повторить этот запрос на zakupki.gov.ru",
                href=_zakupki_rnp_search_url(resolved_inn),
            )
        )
    return ReportSection(title="Реестр недобросовестных поставщиков (РНП)", rows=rows)


def _website_section(website: str) -> ReportSection:
    """Display-only - this feature doesn't analyze the domain itself, the live UI links
    it out to `domain_finder`'s own WHOIS/DNS/CT analysis instead. In an exported report
    there's no live app session to link into, so this links directly to the site itself."""
    return ReportSection(
        title="Домен компании",
        rows=[ReportRow("Сайт", website, href=f"https://{website}")],
    )


def build_sections(search: RuBusinessCheckSearch) -> list[ReportSection]:
    sections = [_summary_section(search)]
    director_name = (search.egrul_data or {}).get("director_name")

    if search.egrul_data:
        sections.append(_egrul_section(search.egrul_data))
    if search.disqualification_result and search.disqualification_result.get("checked"):
        sections.append(_disqualification_section(search.disqualification_result, director_name))
    if search.arbitration_data and search.arbitration_data.get("checked"):
        sections.append(_arbitration_section(search.arbitration_data.get("cases") or []))
    if search.fedresurs_data and search.fedresurs_data.get("checked"):
        sections.append(_fedresurs_section(search.fedresurs_data))
    if search.pb_nalog_data and search.pb_nalog_data.get("checked"):
        sections.append(_pb_nalog_section(search.pb_nalog_data))
    if search.fedsfm_result and search.fedsfm_result.get("checked"):
        sections.append(_fedsfm_section(search.fedsfm_result, director_name))
    if search.rnp_data and search.rnp_data.get("checked"):
        sections.append(_rnp_section(search.rnp_data, search.resolved_inn))
    if search.website:
        sections.append(_website_section(search.website))

    return sections


def generate_ru_business_check_report(
    search: RuBusinessCheckSearch, fmt: str
) -> tuple[bytes, str, str]:
    """Generate an HTML/PDF report for a RU Business Check scan.

    Returns (content, media_type, filename).
    """
    sections = build_sections(search)
    content, media_type = generate_report(REPORT_TITLE, sections, fmt, "ru", GENERATED_AT_LABEL)
    ext = EXPORT_FORMATS[fmt][1]
    safe_query = re.sub(r"[^A-Za-z0-9._-]+", "_", search.query)[:80]
    filename = f"ru-business-check-{search.id}-{safe_query}{ext}"
    return content, media_type, filename
