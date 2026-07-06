from app.core.reports.renderer import render_html, render_pdf
from app.core.reports.schemas import ReportSection

# format -> (media type, file extension)
EXPORT_FORMATS: dict[str, tuple[str, str]] = {
    "html": ("text/html", ".html"),
    "pdf": ("application/pdf", ".pdf"),
}


def generate_report(
    title: str,
    sections: list[ReportSection],
    fmt: str,
    locale: str = "en",
    generated_at_label: str = "Generated at",
) -> tuple[bytes, str]:
    """Render a report as HTML or PDF from already-localized, human-readable sections.

    Returns (content, media_type). Raises ValueError for an unsupported format.
    """
    if fmt not in EXPORT_FORMATS:
        raise ValueError(f"Unsupported export format: {fmt}")

    media_type, _ext = EXPORT_FORMATS[fmt]
    html = render_html(title, sections, locale, generated_at_label)

    if fmt == "html":
        return html.encode("utf-8"), media_type
    return render_pdf(html), media_type
