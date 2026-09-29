"""Regression guard for scan-reconciliation coverage. `reconcile_stale_scans` in
`app.utils.scan_reconciliation_registry` is the single place that knows about every
scan-style feature's `interrupt_running_searches` crud function (see that module's
docstring, and router_registry.py/scheduler_registry.py for the same pattern applied
to routers/scheduler jobs).

This walks every `app/features/*/crud/*.py` file for a `def interrupt_running_searches`
and fails if the module defining it isn't imported by the registry - so a new scan
feature that adds the function but forgets to register it fails a test instead of
silently leaving its stale runs stuck at 'running' forever after a restart.
"""

import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
REGISTRY_PATH = APP_ROOT / "utils" / "scan_reconciliation_registry.py"

_INTERRUPT_FN_RE = re.compile(r"async def interrupt_running_searches\(")


def _iter_crud_files():
    for path in APP_ROOT.glob("features/*/crud/*.py"):
        yield path.relative_to(APP_ROOT).as_posix(), path


def _module_path(rel: str) -> str:
    return "app." + rel[: -len(".py")].replace("/", ".")


def test_every_interrupt_running_searches_is_registered():
    registry_source = REGISTRY_PATH.read_text(encoding="utf-8")

    unregistered = []
    for rel, path in _iter_crud_files():
        if not _INTERRUPT_FN_RE.search(path.read_text(encoding="utf-8")):
            continue
        if _module_path(rel) not in registry_source:
            unregistered.append(rel)

    assert not unregistered, (
        f"crud module(s) define interrupt_running_searches but aren't imported by "
        f"{REGISTRY_PATH.relative_to(APP_ROOT.parent)}: {unregistered}. Add them to "
        "_SCAN_FEATURES there, or stale runs from that feature will never be reconciled "
        "after a restart."
    )


def test_registry_entries_still_exist_and_still_expose_the_function():
    """Keeps the registry itself honest: an entry pointing at a module that no longer
    defines interrupt_running_searches (renamed/removed) should be caught here."""
    registry_source = REGISTRY_PATH.read_text(encoding="utf-8")

    stale = []
    for rel, path in _iter_crud_files():
        module_path = _module_path(rel)
        if module_path not in registry_source:
            continue
        if not _INTERRUPT_FN_RE.search(path.read_text(encoding="utf-8")):
            stale.append(rel)

    assert not stale, f"Registry references module(s) that no longer define the function: {stale}"
