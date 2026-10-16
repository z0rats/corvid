from app.features.image_tools.schemas.image_schemas import GeoCandidate, TextSignal
from app.features.image_tools.service import geo_clues_service


def _candidate(location: str) -> GeoCandidate:
    return GeoCandidate(location=location, confidence=0.5, reasoning="r")


class TestCountriesInText:
    def test_finds_country_inside_a_longer_phrase(self):
        assert geo_clues_service.countries_in_text("Southern Serbia (Vojvodina)") == ["RS"]

    def test_longest_name_wins_over_embedded_shorter_one(self):
        assert geo_clues_service.countries_in_text("Papua New Guinea highlands") == ["PG"]

    def test_whole_words_only(self):
        assert "NG" in geo_clues_service.countries_in_text("Nigeria")
        assert geo_clues_service.countries_in_text("Serbian-looking town") == []

    def test_uses_aliases_and_table_spellings(self):
        assert geo_clues_service.countries_in_text("USA") == ["US"]
        assert geo_clues_service.countries_in_text("Ivory Coast") == ["CI"]
        assert geo_clues_service.countries_in_text("Northern England") == ["GB"]

    def test_generic_region_names_match_nothing(self):
        assert geo_clues_service.countries_in_text("Western Europe") == []


class TestReferenceCountries:
    def test_candidates_come_first_then_text_signals_deduplicated(self):
        signals = [
            TextSignal(
                kind="script",
                matched="Cyrillic",
                source_text="x",
                countries=["RU", "RS"],
                strength="medium",
            )
        ]
        isos = geo_clues_service.reference_countries([_candidate("Serbia")], signals)
        assert isos == ["RS", "RU"]  # KZ has no reference row

    def test_broad_text_signals_add_no_rows(self):
        signals = [
            TextSignal(
                kind="script",
                matched="Cyrillic",
                source_text="x",
                countries=["RU", "UA", "BY", "BG"],
                strength="medium",
            )
        ]
        assert geo_clues_service.reference_countries([_candidate("Somewhere")], signals) == []

    def test_weak_text_signals_are_ignored(self):
        signals = [
            TextSignal(kind="word", matched="x", source_text="x", countries=["FR"], strength="weak")
        ]
        assert geo_clues_service.reference_countries([_candidate("Somewhere")], signals) == []

    def test_only_top_candidates_and_capped_rows(self):
        candidates = [_candidate(n) for n in ("Serbia", "Croatia", "Hungary", "Austria")]
        isos = geo_clues_service.reference_countries(candidates, [])
        assert isos == ["RS", "HR", "HU"]


def test_format_reference_lists_known_fields_and_skips_undocumented_ones():
    text = geo_clues_service.format_reference(["RS", "TH"])
    assert text.startswith("Serbia (RS)\n  Drive: R")
    assert "Thailand (TH)" in text
    assert "—" not in text


def test_every_clue_row_is_complete():
    for iso, row in geo_clues_service._clues().items():
        assert len(iso) == 2
        for key in ("name", "drive", "plates", "paint", "script", "tells", "region"):
            assert row[key], (iso, key)
