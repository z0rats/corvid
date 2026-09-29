import re

from app.core.reports.schemas import ReportRow, ReportSection
from app.core.reports.service import EXPORT_FORMATS, generate_report

from ..models.geolocation_history_models import ImageGeolocationSearch

# RU labels intentionally omitted for now (new-feature i18n is paused) - `locale="ru"`
# falls back to English rather than erroring.
LABELS: dict[str, str] = {
    "report_title": "AI Photo Geolocation Report",
    "generated_at": "Generated at",
    "search_info": "Photo",
    "filename": "Filename",
    "model_used": "Model",
    "searched_at": "Analyzed at",
    "candidates": "Candidate locations",
    "clues": "Visual clues",
    "caveats": "Caveats",
}


def build_sections(search: ImageGeolocationSearch) -> list[ReportSection]:
    t = LABELS
    result = search.result

    search_section = ReportSection(
        title=t["search_info"],
        rows=[
            ReportRow(t["filename"], search.filename),
            ReportRow(t["model_used"], search.model_used),
            ReportRow(t["searched_at"], search.searched_at.strftime("%Y-%m-%d %H:%M UTC")),
        ],
    )

    candidates_section = ReportSection(
        title=t["candidates"],
        rows=[
            ReportRow(
                candidate["location"],
                f"[{candidate['confidence']:.0%}] {candidate['reasoning']}",
            )
            for candidate in result.get("candidates", [])
        ],
    )

    clues_section = ReportSection(
        title=t["clues"],
        rows=[
            ReportRow(clue["category"], f"{clue['observation']} -> {clue['supports']}")
            for clue in result.get("clues", [])
        ],
    )

    sections = [search_section, candidates_section, clues_section]

    caveats = result.get("caveats")
    if caveats:
        sections.append(ReportSection(title=t["caveats"], rows=[ReportRow("", caveats)]))

    return sections


def generate_geolocation_report(search: ImageGeolocationSearch, fmt: str) -> tuple[bytes, str, str]:
    """Generate an HTML/PDF report for a past AI geolocation analysis.

    Returns (content, media_type, filename).
    """
    t = LABELS
    sections = build_sections(search)
    content, media_type = generate_report(t["report_title"], sections, fmt, "en", t["generated_at"])
    ext = EXPORT_FORMATS[fmt][1]
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "_", search.filename)[:80]
    filename = f"geolocation-{search.id}-{safe_filename}{ext}"
    return content, media_type, filename
