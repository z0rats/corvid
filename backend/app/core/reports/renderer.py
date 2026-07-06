import datetime
import io

from jinja2 import Environment
from xhtml2pdf import pisa

from app.core.reports.schemas import ReportSection

_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ locale }}">
<head>
<meta charset="utf-8">
<title>{{ title }}</title>
<style>
  body { font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #1a1a1a; }
  h1 { font-size: 18px; margin-bottom: 4px; }
  .generated-at { color: #666; font-size: 9px; margin-bottom: 20px; }
  h2 { font-size: 13px; margin-top: 20px; margin-bottom: 6px; border-bottom: 1px solid #ccc; padding-bottom: 3px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }
  td { padding: 4px 6px; vertical-align: top; border-bottom: 1px solid #eee; }
  td.label { width: 25%; font-weight: bold; color: #444; white-space: nowrap; }
</style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="generated-at">{{ generated_at_label }}: {{ generated_at }}</div>
  {% for section in sections %}
  <h2>{{ section.title }}</h2>
  <table>
    {% for row in section.rows %}
    <tr>
      <td class="label">{{ row.label }}</td>
      <td>{{ row.value }}</td>
    </tr>
    {% endfor %}
  </table>
  {% endfor %}
</body>
</html>
"""

_env = Environment(autoescape=True)
_template = _env.from_string(_TEMPLATE)


def render_html(title: str, sections: list[ReportSection], locale: str, generated_at_label: str) -> str:
    return _template.render(
        title=title,
        sections=sections,
        locale=locale,
        generated_at_label=generated_at_label,
        generated_at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def render_pdf(html: str) -> bytes:
    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8")
    if result.err:
        raise ValueError(f"PDF generation failed with {result.err} error(s)")
    return buffer.getvalue()
