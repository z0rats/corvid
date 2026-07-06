from app.core.reports.schemas import ReportRow, ReportSection
from app.core.reports.service import EXPORT_FORMATS, generate_report
from app.features.email_analyzer.schemas.email_schemas import EmailAnalysisResponse

LABELS: dict[str, dict[str, str]] = {
    "en": {
        "report_title": "Email Analysis Report",
        "generated_at": "Generated at",
        "basic_info": "Basic info",
        "from": "From",
        "to": "To",
        "cc": "CC",
        "subject": "Subject",
        "date": "Date",
        "message_id": "Message-ID",
        "hashes": "File hashes",
        "warnings": "Security warnings",
        "attachments": "Attachments",
        "hops": "Routing hops",
        "urls": "URLs found",
        "no_warnings": "No warnings",
        "no_attachments": "No attachments",
        "no_urls": "No URLs found",
    },
    "ru": {
        "report_title": "Отчёт по анализу письма",
        "generated_at": "Сформирован",
        "basic_info": "Основная информация",
        "from": "От",
        "to": "Кому",
        "cc": "Копия",
        "subject": "Тема",
        "date": "Дата",
        "message_id": "Message-ID",
        "hashes": "Хеши файла",
        "warnings": "Предупреждения безопасности",
        "attachments": "Вложения",
        "hops": "Маршрут письма",
        "urls": "Найденные URL",
        "no_warnings": "Предупреждений нет",
        "no_attachments": "Вложений нет",
        "no_urls": "URL не найдены",
    },
}


def _labels(locale: str) -> dict[str, str]:
    return LABELS.get(locale, LABELS["en"])


def build_sections(result: EmailAnalysisResponse, locale: str) -> list[ReportSection]:
    t = _labels(locale)
    info = result.basic_info

    basic_section = ReportSection(
        title=t["basic_info"],
        rows=[
            ReportRow(t["from"], info.from_address or "-"),
            ReportRow(t["to"], info.to_address or "-"),
            ReportRow(t["cc"], info.cc or "-"),
            ReportRow(t["subject"], info.subject or "-"),
            ReportRow(t["date"], info.date or "-"),
            ReportRow(t["message_id"], info.message_id or "-"),
        ],
    )

    hashes_section = ReportSection(
        title=t["hashes"],
        rows=[
            ReportRow("MD5", result.eml_hashes.md5),
            ReportRow("SHA1", result.eml_hashes.sha1),
            ReportRow("SHA256", result.eml_hashes.sha256),
        ],
    )

    warnings_section = ReportSection(
        title=t["warnings"],
        rows=[
            ReportRow(f"[{w.warning_tlp.value.upper()}] {w.warning_title}", w.warning_message)
            for w in result.warnings
        ]
        or [ReportRow("-", t["no_warnings"])],
    )

    attachments_section = ReportSection(
        title=t["attachments"],
        rows=[
            ReportRow(a.filename, f"MD5: {a.md5} | SHA1: {a.sha1} | SHA256: {a.sha256}")
            for a in result.attachments
        ]
        or [ReportRow("-", t["no_attachments"])],
    )

    hops_section = ReportSection(
        title=t["hops"],
        rows=[
            ReportRow(f"#{hop.number}", f"{hop.from_server or '-'} -> {hop.by_server or '-'} ({hop.with_protocol or '-'})")
            for hop in result.hops
        ],
    )

    urls_section = ReportSection(
        title=t["urls"],
        rows=[ReportRow(str(i + 1), url) for i, url in enumerate(result.urls)] or [ReportRow("-", t["no_urls"])],
    )

    return [basic_section, hashes_section, warnings_section, attachments_section, hops_section, urls_section]


def generate_analysis_report(result: EmailAnalysisResponse, fmt: str, locale: str = "en") -> tuple[bytes, str, str]:
    """Generate an HTML/PDF report for an email analysis result.

    Returns (content, media_type, filename).
    """
    t = _labels(locale)
    sections = build_sections(result, locale)
    content, media_type = generate_report(t["report_title"], sections, fmt, locale, t["generated_at"])
    ext = EXPORT_FORMATS[fmt][1]
    filename = f"email-analysis{ext}"
    return content, media_type, filename
