"""Regression guard for scan-reconciliation coverage. `reconcile_stale_scans` in
`app.utils.scan_reconciliation_registry` is the single place that knows about every scan
feature (see that module's docstring, and router_registry.py/scheduler_registry.py for the
same pattern applied to routers/scheduler jobs).

Every `ScanFeature` declared anywhere under `app/features/` must be in its `_SCAN_FEATURES`
- otherwise a new scan feature's runs interrupted by a restart stay 'running' forever.
Checked on the live objects (imported, not grepped), so a renamed constant can't slip by.
"""

import importlib
from pathlib import Path

from app.core.scans.feature import ScanFeature
from app.utils.scan_reconciliation_registry import _SCAN_FEATURES

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def _declared_scan_features() -> dict[str, ScanFeature]:
    found = {}
    for path in APP_ROOT.glob("features/**/*.py"):
        if "ScanFeature(" not in path.read_text(encoding="utf-8"):
            continue
        module_name = "app." + path.relative_to(APP_ROOT).with_suffix("").as_posix().replace(
            "/", "."
        )
        module = importlib.import_module(module_name)
        for attr, value in vars(module).items():
            if isinstance(value, ScanFeature):
                found[f"{module_name}.{attr}"] = value
    return found


def test_every_declared_scan_feature_is_registered():
    declared = _declared_scan_features()
    assert declared, "no ScanFeature found under app/features - the walk itself is broken"
    unregistered = [name for name, feature in declared.items() if feature not in _SCAN_FEATURES]
    assert not unregistered, (
        f"ScanFeature(s) not in app/utils/scan_reconciliation_registry.py's _SCAN_FEATURES: "
        f"{unregistered}. Add them, or stale runs from that feature will never be reconciled "
        "after a restart."
    )


def test_one_scan_feature_per_table():
    """`ScanRun`'s cancel registry and reconciliation are keyed by table - two
    `ScanFeature`s over one model would split them."""
    models = [feature.model for feature in _SCAN_FEATURES]
    assert len(models) == len(set(models))
