"""requirements-dev.txt must pin every runtime package at the exact version requirements.txt does.

The Docker image installs only requirements.txt; CI and local venvs install requirements-dev.txt
(runtime + test/lint tools). If the two drift - e.g. a dependency bump regenerates one lock but
not the other - CI would test different versions than the image ships. Regenerate both:
`uv pip compile requirements.in -o requirements.txt` then
`uv pip compile requirements-dev.in -o requirements-dev.txt`.
"""

import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
_PIN = re.compile(r"^([A-Za-z0-9._-]+)(?:\[[^\]]*\])?==(\S+)")


def _pins(name: str) -> dict[str, str]:
    pins = {}
    for line in (BACKEND_DIR / name).read_text().splitlines():
        match = _PIN.match(line)
        if match:
            pins[match.group(1).lower().replace("_", "-")] = match.group(2)
    return pins


def test_dev_lock_pins_every_runtime_package_at_the_same_version():
    runtime = _pins("requirements.txt")
    dev = _pins("requirements-dev.txt")

    assert runtime, "requirements.txt has no pins - parse broke?"
    mismatched = {
        pkg: (version, dev.get(pkg)) for pkg, version in runtime.items() if dev.get(pkg) != version
    }
    assert mismatched == {}, f"(requirements.txt, requirements-dev.txt) disagree: {mismatched}"


def test_runtime_lock_has_no_dev_only_tools():
    runtime = _pins("requirements.txt")
    assert not {"pytest", "pytest-cov", "mypy", "ruff"} & runtime.keys()
