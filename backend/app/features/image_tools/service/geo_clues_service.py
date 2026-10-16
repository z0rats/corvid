"""Per-country reference clues for the geolocation cross-check pass.

`lookup_data/country_clues.json` holds one row per country (driving side, plate format, road paint,
script, other strong tells), extracted from GeoInt's world clue library (see
`lookup_data/NOTICE.md`). Only the rows for countries already in play are handed to the model, so
the prompt stays small enough for local models with short context windows.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from ..schemas.image_schemas import GeoCandidate, TextSignal
from .text_signals_service import country_table

_DATA_DIR = Path(__file__).resolve().parent.parent / "lookup_data"

# Top candidates whose country is looked up, and the cap on rows sent for the second pass.
_MAX_CANDIDATES = 3
_MAX_ROWS = 8
_STRONG_STRENGTHS = {"strong", "medium"}
# A signal naming more countries than this (euro, Cyrillic) is too broad to add reference rows.
_MAX_SIGNAL_COUNTRIES = 3
# Names models commonly use that neither table spells this way.
_ALIASES = {
    "US": ("USA", "United States of America", "U.S.", "U.S.A."),
    "GB": ("UK", "U.K.", "Great Britain", "England", "Scotland", "Wales", "Northern Ireland"),
    "RU": ("Russian Federation",),
    "CZ": ("Czech Republic", "Czechia"),
    "TR": ("Turkiye", "Türkiye"),
    "KR": ("Republic of Korea",),
    "AE": ("United Arab Emirates",),
    "MM": ("Burma",),
}
_COLUMNS = (
    ("drive", "Drive"),
    ("plates", "Plates"),
    ("paint", "Road paint (centre / edge)"),
    ("script", "Script / language"),
    ("tells", "Other strong tells"),
)


@lru_cache(maxsize=1)
def _clues() -> dict[str, dict[str, str]]:
    return json.loads((_DATA_DIR / "country_clues.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _name_patterns() -> list[tuple[re.Pattern[str], str]]:
    """(whole-word pattern, ISO) pairs, longest names first so 'Papua New Guinea' wins."""
    names: list[tuple[str, str]] = []
    for iso, row in _clues().items():
        spellings = {
            row["name"],
            country_table().get(iso, {}).get("name", ""),
            *_ALIASES.get(iso, ()),
        }
        names.extend((name, iso) for name in spellings if name)
    names.sort(key=lambda pair: len(pair[0]), reverse=True)
    return [
        (re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", re.IGNORECASE), iso) for name, iso in names
    ]


def countries_in_text(text: str) -> list[str]:
    """ISO codes of countries named in free text such as 'Southern Serbia (Vojvodina)'."""
    found: list[str] = []
    remaining = text
    for pattern, iso in _name_patterns():
        if pattern.search(remaining):
            found.append(iso)
            remaining = pattern.sub(" ", remaining)
    return found


def reference_countries(
    candidates: list[GeoCandidate], text_signals: list[TextSignal]
) -> list[str]:
    """Countries to cross-check: top candidates first, then countries the text points to."""
    isos: list[str] = []
    for candidate in candidates[:_MAX_CANDIDATES]:
        isos.extend(countries_in_text(candidate.location))
    for signal in text_signals:
        if signal.strength in _STRONG_STRENGTHS and len(signal.countries) <= _MAX_SIGNAL_COUNTRIES:
            isos.extend(signal.countries)
    known = _clues()
    unique = list(dict.fromkeys(iso for iso in isos if iso in known))
    return unique[:_MAX_ROWS]


def format_reference(isos: list[str]) -> str:
    """Render the reference rows as plain text blocks for the prompt."""
    blocks = []
    for iso in isos:
        row = _clues()[iso]
        lines = [f"{row['name']} ({iso})"]
        lines.extend(f"  {label}: {row[key]}" for key, label in _COLUMNS if row[key] != "—")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
