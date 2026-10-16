"""Deterministic country/language hints from text transcribed out of a photo.

The vision model transcribes what it can read (`visible_text`); everything here is plain table
lookups over `lookup_data/` (see `lookup_data/NOTICE.md`), so a hint is checkable rather than
model opinion. Signals narrow languages and plausible countries, not borders - minorities,
tourists, diaspora shops and imported goods all carry scripts and words abroad.
"""

import json
import re
import unicodedata
from collections.abc import Sequence
from functools import cache
from pathlib import Path

from ..schemas.image_schemas import TextSignal, TextSignalKind

DATA_DIR = Path(__file__).resolve().parent.parent / "lookup_data"

# Cap per kind so one noisy transcription cannot bury the useful hints.
_MAX_SIGNALS_PER_KIND = 8
# A calling-code prefix shared by more countries than this (e.g. +1) says too little to report.
_MAX_PHONE_PREFIX_COUNTRIES = 2
# The transcription is model output: bound the work a runaway or hostile one can cause.
_MAX_LINES = 100
_MAX_LINE_LENGTH = 300

_STRENGTH_ORDER = {"strong": 0, "medium": 1, "weak": 2}
_SCRIPT_NAME_ALIASES = {"HALFWIDTH KATAKANA": "KATAKANA", "HALFWIDTH HANGUL": "HANGUL"}
_PHONE_RE = re.compile(r"\+\s?(\d[\d\s().-]{5,})")
_DOMAIN_RE = re.compile(r"(?:[a-z0-9-]+\.)+([a-z]{2})(?![a-z0-9-])")
_WORD_RE = re.compile(r"[^\W\d_]+")


@cache
def _signals_table() -> dict:
    return json.loads((DATA_DIR / "text_signals.json").read_text(encoding="utf-8"))


@cache
def _keys_longest_first(section: str) -> tuple[str, ...]:
    """A signals-table section's keys, longest first so a more specific name wins a prefix match.
    Cached: the table never changes at runtime, and this ran once per transcribed line."""
    return tuple(sorted(_signals_table()[section], key=len, reverse=True))


@cache
def country_table() -> dict[str, dict]:
    return json.loads((DATA_DIR / "country_info.json").read_text(encoding="utf-8"))


@cache
def _tld_to_country() -> dict[str, str]:
    return {
        info["tld"].lstrip(".").lower(): iso
        for iso, info in country_table().items()
        if info.get("tld")
    }


@cache
def _phone_prefixes() -> dict[str, list[str]]:
    """Calling-code digit string -> ISO codes. Entries like '+1-809 and 1-829' list several."""
    prefixes: dict[str, list[str]] = {}
    for iso, info in country_table().items():
        for token in re.findall(r"\+?(\d[\d-]*)", info.get("phone", "")):
            prefixes.setdefault(token.replace("-", ""), []).append(iso)
    return prefixes


def _normalize(text: str) -> str:
    """Lowercase and strip accents so 'Bäckerei' and 'backerei' compare equal."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _script_of(char: str, keys: Sequence[str]) -> str | None:
    name = unicodedata.name(char, "")
    for alias, key in _SCRIPT_NAME_ALIASES.items():
        if name.startswith(alias):
            return key
    for key in keys:
        if name == key or name.startswith(f"{key} "):
            return key
    return None


def _digit_script_of(char: str, keys: Sequence[str]) -> str | None:
    name = unicodedata.name(char, "")
    for key in keys:
        if name.startswith(f"{key} DIGIT"):
            return key
    return None


class _Collector:
    """Collects signals, keeping the first occurrence of each (kind, matched) pair."""

    def __init__(self) -> None:
        self._seen: set[tuple[TextSignalKind, str]] = set()
        self._per_kind: dict[str, int] = {}
        self.signals: list[TextSignal] = []

    def add(self, kind: TextSignalKind, matched: str, source_text: str, **fields) -> None:
        key = (kind, matched)
        if key in self._seen or self._per_kind.get(kind, 0) >= _MAX_SIGNALS_PER_KIND:
            return
        self._seen.add(key)
        self._per_kind[kind] = self._per_kind.get(kind, 0) + 1
        self.signals.append(
            TextSignal(kind=kind, matched=matched, source_text=source_text, **fields)
        )


def _scan_characters(line: str, out: _Collector) -> None:
    table = _signals_table()
    script_keys = _keys_longest_first("scripts")
    digit_keys = _keys_longest_first("digits")
    for char in line:
        if char.isdigit():
            digit_key = _digit_script_of(char, digit_keys)
            if digit_key:
                entry = table["digits"][digit_key]
                out.add(
                    "digits",
                    digit_key.title(),
                    line,
                    countries=entry.get("countries", []),
                    strength="medium",
                    note=entry.get("note"),
                )
            continue
        letter = table["letters"].get(char.lower())
        if letter:
            out.add(
                "letter",
                char.lower(),
                line,
                languages=letter.get("langs", []),
                strength="medium",
                note=letter.get("note"),
            )
        script_key = _script_of(char, script_keys) if not char.isascii() else None
        if script_key:
            entry = table["scripts"][script_key]
            out.add(
                "script",
                script_key.title(),
                line,
                countries=entry.get("countries", []),
                strength=entry.get("strength", "medium"),
                note=entry.get("note"),
            )


@cache
def _currency_regex(pattern: str) -> re.Pattern[str]:
    escaped = re.escape(pattern)
    if pattern.isascii() and any(c.isalpha() for c in pattern):
        # Short alphabetic marks ('kr', 'Q', 'KM') only count next to a number.
        return re.compile(
            rf"(?<![A-Za-z])\d[\d.,]*\s?{escaped}(?![A-Za-z])|(?<![A-Za-z]){escaped}\s?\d"
        )
    return re.compile(escaped)


def _scan_currency(line: str, out: _Collector) -> None:
    for entry in _signals_table()["currency"]:
        pattern = entry["pattern"]
        if _currency_regex(pattern).search(line):
            out.add(
                "currency",
                pattern,
                line,
                countries=entry.get("countries", []),
                strength="weak" if len(entry.get("countries", [])) > 4 else "medium",
                note=entry.get("note"),
            )


def _scan_domains(line: str, out: _Collector) -> None:
    vanity = set(_signals_table()["vanity_tlds"])
    for match in _DOMAIN_RE.finditer(line.lower()):
        tld = match.group(1)
        iso = _tld_to_country().get(tld)
        if iso and tld not in vanity:
            out.add("domain", f".{tld}", line, countries=[iso], strength="medium")


def _scan_phones(line: str, out: _Collector) -> None:
    for match in _PHONE_RE.finditer(line):
        digits = re.sub(r"\D", "", match.group(1))
        for length in range(min(4, len(digits)), 0, -1):
            countries = _phone_prefixes().get(digits[:length])
            if countries:
                if len(countries) <= _MAX_PHONE_PREFIX_COUNTRIES:
                    out.add(
                        "phone",
                        f"+{digits[:length]}",
                        line,
                        countries=countries,
                        strength="strong" if len(countries) == 1 else "medium",
                    )
                break


def _scan_words(line: str, out: _Collector) -> None:
    words = _signals_table()["words"]
    normalized = _normalize(line)
    tokens = _WORD_RE.findall(normalized)
    # Multi-word entries ('sari sari') are matched on the joined token stream.
    haystack = f" {' '.join(tokens)} "
    for word, entry in words.items():
        if word.startswith("_") or not isinstance(entry, dict):
            continue
        if f" {word} " in haystack:
            out.add(
                "word",
                word,
                line,
                countries=entry.get("countries", []),
                languages=entry.get("langs", []),
                strength="strong" if entry.get("countries") else "weak",
                note=entry.get("note"),
            )


def compute_text_signals(visible_text: list[str]) -> list[TextSignal]:
    """Country/language hints for each transcribed line, deduplicated across lines."""
    out = _Collector()
    for line in visible_text[:_MAX_LINES]:
        line = line.strip()[:_MAX_LINE_LENGTH]
        if not line:
            continue
        _scan_characters(line, out)
        _scan_currency(line, out)
        _scan_domains(line, out)
        _scan_phones(line, out)
        _scan_words(line, out)
    # Most telling first; the sort is stable, so equal strengths keep reading order.
    return sorted(out.signals, key=lambda s: _STRENGTH_ORDER[s.strength])
