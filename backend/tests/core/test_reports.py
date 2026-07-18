import pytest

from app.core.reports.renderer import render_html, render_pdf
from app.core.reports.schemas import ReportRow, ReportSection
from app.core.reports.service import generate_report

# --- render_html --------------------------------------------------------


def test_render_html_escapes_malicious_row_values():
    # Report values often echo back attacker/target-controlled data (a
    # phishing email's subject, an untrusted header) - Jinja2 autoescape
    # must actually neutralize it, not just "not crash".
    sections = [ReportSection(title="Findings", rows=[ReportRow(label="Subject", value="<script>alert(1)</script>")])]

    html = render_html("Report", sections, locale="en", generated_at_label="Generated at")

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_render_html_escapes_malicious_section_title_and_report_title():
    sections = [ReportSection(title='"><img src=x onerror=alert(1)>', rows=[])]

    html = render_html('Report <b>title</b>', sections, locale="en", generated_at_label="Generated at")

    assert "<img src=x onerror=alert(1)>" not in html
    assert "Report <b>title</b>" not in html


def test_render_html_sets_lang_attribute_from_locale():
    html_en = render_html("Report", [], locale="en", generated_at_label="Generated at")
    html_ru = render_html("Report", [], locale="ru", generated_at_label="Generated at")

    assert '<html lang="en">' in html_en
    assert '<html lang="ru">' in html_ru


def test_render_html_includes_generated_at_label_and_timestamp():
    html = render_html("Report", [], locale="en", generated_at_label="Сгенерировано в")

    assert "Сгенерировано в" in html
    assert "UTC" in html


def test_render_html_renders_all_sections_and_rows_in_order():
    sections = [
        ReportSection(title="Section A", rows=[ReportRow(label="k1", value="v1"), ReportRow(label="k2", value="v2")]),
        ReportSection(title="Section B", rows=[ReportRow(label="k3", value="v3")]),
    ]

    html = render_html("Report", sections, locale="en", generated_at_label="Generated at")

    assert html.index("Section A") < html.index("k1") < html.index("k2") < html.index("Section B") < html.index("k3")


def test_render_html_handles_empty_sections_list_without_error():
    html = render_html("Report", [], locale="en", generated_at_label="Generated at")

    assert "<h1>Report</h1>" in html
    assert "<h2>" not in html


def test_render_html_handles_section_with_no_rows():
    sections = [ReportSection(title="Empty Section", rows=[])]

    html = render_html("Report", sections, locale="en", generated_at_label="Generated at")

    assert "<h2>Empty Section</h2>" in html
    assert "<tr>" not in html


# --- render_pdf -----------------------------------------------------------
#
# xhtml2pdf/pisa is very lenient: empirically it does not set result.err (and
# therefore render_pdf never raises ValueError) even for empty, malformed, or
# None input - it just best-effort renders whatever it's given. So these
# tests only assert the one guarantee that actually holds: real, well-formed
# HTML produces non-empty PDF bytes starting with the PDF magic header.


def test_render_pdf_produces_non_empty_pdf_bytes():
    html = render_html("Report", [ReportSection(title="A", rows=[ReportRow(label="k", value="v")])], "en", "Generated at")

    pdf_bytes = render_pdf(html)

    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


# --- generate_report --------------------------------------------------


def test_generate_report_html_format_returns_utf8_encoded_bytes():
    sections = [ReportSection(title="A", rows=[ReportRow(label="k", value="v")])]

    content, media_type = generate_report("Report", sections, fmt="html")

    assert media_type == "text/html"
    assert content.decode("utf-8") == render_html("Report", sections, locale="en", generated_at_label="Generated at")


def test_generate_report_pdf_format_returns_pdf_bytes():
    sections = [ReportSection(title="A", rows=[ReportRow(label="k", value="v")])]

    content, media_type = generate_report("Report", sections, fmt="pdf")

    assert media_type == "application/pdf"
    assert content.startswith(b"%PDF")


def test_generate_report_rejects_unsupported_format():
    with pytest.raises(ValueError, match="docx"):
        generate_report("Report", [], fmt="docx")


def test_generate_report_passes_locale_through_to_html_output():
    content, _media_type = generate_report("Report", [], fmt="html", locale="ru")

    assert '<html lang="ru">' in content.decode("utf-8")
