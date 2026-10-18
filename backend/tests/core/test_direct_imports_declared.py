"""Every third-party package `app/` imports must be a direct requirement in requirements.in.

A package that only arrives transitively (e.g. numpy via some unrelated library's pandas) works
until that library is dropped or changes its own dependencies - then the import breaks at
runtime, with nothing in the lock diff pointing at it. Declare it in requirements.in instead.
"""

import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
SKIPPED = {"app", "main", "migrations", *sys.stdlib_module_names}
# Reached through a declared requirement on purpose, not by accident:
TRANSITIVE_BY_DESIGN = {
    "starlette": "FastAPI is built on it and re-exports it - they move together",
    "xhtml2pdf": "maigret[pdf]'s extra is the declared source of the PDF stack core/reports uses",
}
_REQUIREMENT = re.compile(r"^([A-Za-z0-9._-]+)")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared() -> set[str]:
    declared = set()
    for line in (BACKEND_DIR / "requirements.in").read_text().splitlines():
        match = _REQUIREMENT.match(line.strip())
        if match:
            declared.add(_normalize(match.group(1)))
    return declared


def _imported_top_level_modules() -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for path in [BACKEND_DIR / "main.py", *(BACKEND_DIR / "app").rglob("*.py")]:
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                modules.setdefault(name.split(".")[0], path)
    return modules


def test_every_third_party_import_is_a_direct_requirement():
    declared = _declared()
    module_to_dists = packages_distributions()

    undeclared = {}
    for module, path in _imported_top_level_modules().items():
        if module in SKIPPED or module in TRANSITIVE_BY_DESIGN:
            continue
        dists = {_normalize(d) for d in module_to_dists.get(module, [])}
        if not dists & declared:
            first_use = str(path.relative_to(BACKEND_DIR))
            undeclared[module] = (sorted(dists) or "not installed", first_use)

    assert undeclared == {}, (
        f"imported but not in requirements.in (module: (dists, first use)): {undeclared}"
    )
