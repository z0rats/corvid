import re

from app.core.reports.schemas import ReportRow, ReportSection
from app.core.reports.service import EXPORT_FORMATS, generate_report
from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import SingleLookupSearch

LABELS: dict[str, dict[str, str]] = {
    "en": {
        "report_title": "IOC Lookup Report",
        "generated_at": "Generated at",
        "search_info": "Search",
        "ioc": "IOC",
        "ioc_type": "Type",
        "searched_at": "Searched at",
        "results": "Service results",
        "status": "Status",
        "tlp": "TLP",
    },
    "ru": {
        "report_title": "Отчёт по проверке IOC",
        "generated_at": "Сформирован",
        "search_info": "Запрос",
        "ioc": "IOC",
        "ioc_type": "Тип",
        "searched_at": "Дата проверки",
        "results": "Результаты по сервисам",
        "status": "Статус",
        "tlp": "TLP",
    },
}


def _labels(locale: str) -> dict[str, str]:
    return LABELS.get(locale, LABELS["en"])


def build_sections(search: SingleLookupSearch, locale: str) -> list[ReportSection]:
    t = _labels(locale)

    search_section = ReportSection(
        title=t["search_info"],
        rows=[
            ReportRow(t["ioc"], search.ioc),
            ReportRow(t["ioc_type"], search.ioc_type),
            ReportRow(t["searched_at"], search.searched_at.strftime("%Y-%m-%d %H:%M UTC")),
        ],
    )

    results_section = ReportSection(
        title=t["results"],
        rows=[
            ReportRow(
                result.service_name,
                f"[{result.status.upper()}, {t['tlp']}: {result.tlp}] {result.summary}",
            )
            for result in search.results
        ],
    )

    return [search_section, results_section]


def generate_search_report(search: SingleLookupSearch, fmt: str, locale: str = "en") -> tuple[bytes, str, str]:
    """Generate an HTML/PDF report for a single-IOC lookup search.

    Returns (content, media_type, filename).
    """
    t = _labels(locale)
    sections = build_sections(search, locale)
    content, media_type = generate_report(t["report_title"], sections, fmt, locale, t["generated_at"])
    ext = EXPORT_FORMATS[fmt][1]
    safe_ioc = re.sub(r"[^A-Za-z0-9._-]+", "_", search.ioc)[:80]
    filename = f"ioc-lookup-{search.id}-{safe_ioc}{ext}"
    return content, media_type, filename
