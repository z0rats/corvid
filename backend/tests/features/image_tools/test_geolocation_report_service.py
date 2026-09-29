"""geolocation_report_service.build_sections/generate_geolocation_report."""

import datetime

from app.features.image_tools.models.geolocation_history_models import ImageGeolocationSearch
from app.features.image_tools.service.geolocation_report_service import (
    build_sections,
    generate_geolocation_report,
)


def _search(**overrides) -> ImageGeolocationSearch:
    defaults = dict(
        id=1,
        filename="street.jpg",
        image_sha256="a" * 64,
        model_used="claude-sonnet-4-6",
        top_candidate="Serbia",
        top_confidence=0.6,
        result={
            "candidates": [{"location": "Serbia", "confidence": 0.6, "reasoning": "road signs"}],
            "clues": [
                {
                    "category": "signage_language",
                    "observation": "Cyrillic text",
                    "supports": "Serbia/Balkans",
                }
            ],
            "caveats": "Hypothesis only, not confirmed.",
        },
        searched_at=datetime.datetime(2026, 9, 10, 12, 0, tzinfo=datetime.UTC),
    )
    defaults.update(overrides)
    return ImageGeolocationSearch(**defaults)


def _section(sections, title):
    return next(s for s in sections if s.title == title)


class TestBuildSections:
    def test_photo_section_has_filename_model_and_timestamp(self):
        sections = build_sections(_search())
        section = _section(sections, "Photo")
        values = {row.label: row.value for row in section.rows}
        assert values["Filename"] == "street.jpg"
        assert values["Model"] == "claude-sonnet-4-6"
        assert values["Analyzed at"] == "2026-09-10 12:00 UTC"

    def test_candidates_section_includes_confidence_and_reasoning(self):
        section = _section(build_sections(_search()), "Candidate locations")
        row = section.rows[0]
        assert row.label == "Serbia"
        assert "60%" in row.value
        assert "road signs" in row.value

    def test_clues_section_shows_observation_and_support(self):
        section = _section(build_sections(_search()), "Visual clues")
        row = section.rows[0]
        assert row.label == "signage_language"
        assert "Cyrillic text" in row.value
        assert "Serbia/Balkans" in row.value

    def test_caveats_section_present_when_set(self):
        sections = build_sections(_search())
        titles = [s.title for s in sections]
        assert "Caveats" in titles

    def test_no_caveats_section_when_absent(self):
        search = _search(result={**_search().result, "caveats": None})
        sections = build_sections(search)
        titles = [s.title for s in sections]
        assert "Caveats" not in titles

    def test_no_candidates_is_an_empty_section_not_a_missing_one(self):
        search = _search(result={"candidates": [], "clues": [], "caveats": None})
        section = _section(build_sections(search), "Candidate locations")
        assert section.rows == []


class TestGenerateGeolocationReport:
    def test_html_format_produces_utf8_bytes_with_the_top_candidate(self):
        content, media_type, filename = generate_geolocation_report(_search(), "html")

        assert media_type == "text/html"
        html = content.decode("utf-8")
        assert "Serbia" in html
        assert filename == "geolocation-1-street.jpg.html"

    def test_pdf_format_produces_pdf_bytes(self):
        content, media_type, _filename = generate_geolocation_report(_search(), "pdf")

        assert media_type == "application/pdf"
        assert content.startswith(b"%PDF")

    def test_filename_sanitizes_the_original_filename(self):
        search = _search(filename='weird "name" / with spaces.jpg')
        _content, _media_type, filename = generate_geolocation_report(search, "html")

        assert filename.startswith("geolocation-1-")
        assert " " not in filename
        assert "/" not in filename
