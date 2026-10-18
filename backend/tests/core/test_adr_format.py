"""New ADRs must keep their rejected alternatives next to the decision.

An ADR that records only the pick loses the reason each alternative lost, and that alternative
then gets proposed again. `docs/adr/TEMPLATE.md` is the format; ADRs up to `LAST_LEGACY_ADR`
predate it and are exempt rather than rewritten.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ADR_DIR = REPO_ROOT / "docs/adr"
LAST_LEGACY_ADR = 22
REQUIRED_HEADINGS = ("## Decision", "## Rejected")

ADR_RE = re.compile(r"^(\d{4})-.+\.md$")


def _adrs() -> list[tuple[int, Path]]:
    found = []
    for path in sorted(ADR_DIR.iterdir()):
        match = ADR_RE.match(path.name)
        if match:
            found.append((int(match.group(1)), path))
    return found


ADRS = _adrs()
NEW_ADRS = [path for number, path in ADRS if number > LAST_LEGACY_ADR]


def test_adrs_were_discovered():
    assert len(ADRS) >= LAST_LEGACY_ADR, ADRS


def test_adr_numbers_are_unique():
    numbers = [number for number, _ in ADRS]
    assert len(numbers) == len(set(numbers)), sorted(numbers)


@pytest.mark.parametrize("path", NEW_ADRS, ids=lambda p: p.name)
def test_new_adr_has_required_sections(path: Path):
    headings = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    missing = [
        required
        for required in REQUIRED_HEADINGS
        if not any(line == required or line.startswith(required + " ") for line in headings)
    ]
    assert not missing, f"{path.name} lacks {missing}; see docs/adr/TEMPLATE.md"
