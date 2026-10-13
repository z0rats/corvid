"""The user-scanner integration (email -> accounts registered with it, ~150 services).

Unlike mailcat (a username's local part probed at mail providers), user-scanner takes a *full
address* and asks each service whether it has an account for it. See
docs/architecture/email-search.md and docs/adr/0019-user-scanner-email-source.md.

Which modules may run is decided by `user_scanner_manifest.json`, a reviewed snapshot of every
module of the pinned package version, not by user-scanner's own filters: a module that triggers a
password-reset or verification email sends it to the *target*, and upstream's loud list is
hand-maintained (it missed AniList's reset mutation). A module absent from the manifest never runs,
and tests/features/email_search/test_user_scanner_config.py fails until a new one is reviewed.
"""

import json
from functools import lru_cache
from importlib import metadata as importlib_metadata
from pathlib import Path
from types import ModuleType

PACKAGE_NAME = "user-scanner"
MANIFEST_PATH = Path(__file__).with_name("user_scanner_manifest.json")

# user-scanner's own settings file defaults to a path inside the installed package; keep it (and
# anything it persists) in the data dir instead.
CONFIG_ENV_VAR = "USER_SCANNER_CONFIG"


@lru_cache
def load_manifest() -> dict[str, dict]:
    """module stem -> {"category": str, "run": bool, "reason"?: str}"""
    return json.loads(MANIFEST_PATH.read_text())["modules"]


def is_available() -> bool:
    try:
        importlib_metadata.version(PACKAGE_NAME)
    except importlib_metadata.PackageNotFoundError:
        return False
    return True


def get_installed_version() -> str:
    return importlib_metadata.version(PACKAGE_NAME)


def get_runnable_modules() -> list[ModuleType]:
    """Email modules the manifest allows, loaded from the installed package."""
    from user_scanner.core.helpers import load_categories, load_modules

    manifest = load_manifest()
    modules: list[ModuleType] = []
    for path in load_categories(is_email=True).values():
        for module in load_modules(path):
            if manifest.get(module.__name__.split(".")[-1], {}).get("run") is True:
                modules.append(module)
    return modules


def runnable_module_count() -> int:
    return sum(1 for entry in load_manifest().values() if entry["run"])
