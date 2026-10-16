"""Every external source has a live canary or an explicit reason it hasn't
(`tests/canary/coverage_map.py`). Sources are read from the app's live registries - imported
objects, not grepped text - so a new ioc_lookup provider, domain_finder `Provider`,
ru_business_check source, registry dump, blacklist feed, dork engine or phone checker fails this
test until it gets a `Covered`/`Exempt` entry. The fixed-host files from the SSRF allowlist must
each map onto sources, so a new fixed-host client prompts the same decision."""

import importlib
import importlib.util
import pkgutil
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

from app.core.registry_dumps.scheduler import DumpJob
from app.features.dork_runner.service import dork_query_service
from app.features.ioc_tools.domain_finder import service as domain_finder_service
from app.features.ioc_tools.domain_finder.service.provider_http import Provider
from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    blacklist_refresh_service,
    external_api_clients,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import (
    get_all_services,
    register_services,
)
from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS
from app.features.phone_search.config.checkers_config import CHECKERS
from app.features.ru_business_check.config.ru_business_check_config import AVAILABLE_SOURCES
from app.features.ru_business_check.service import (
    registry_dump_scheduler_service as ru_dump_jobs,
)
from app.features.sanctions_search.service import (
    sanctions_search_scheduler_service as sanctions_dump_jobs,
)
from tests.canary import coverage_map
from tests.canary.coverage_map import COVERAGE, EXEMPT_REASONS, Covered, Exempt
from tests.core.test_ssrf_guard_coverage import ALLOWLISTED_FIXED_HOST_FILES

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CANARY_DIR = BACKEND_ROOT / "tests" / "canary"


def _domain_finder_providers() -> set[str]:
    codes = set()
    for info in pkgutil.iter_modules(domain_finder_service.__path__):
        module = importlib.import_module(f"{domain_finder_service.__name__}.{info.name}")
        codes |= {obj.code for obj in vars(module).values() if isinstance(obj, Provider)}
    return codes


def _dump_jobs() -> list[DumpJob]:
    return ru_dump_jobs.dump_jobs() + sanctions_dump_jobs.dump_jobs()


def _blacklist_feeds() -> set[str]:
    return {
        name.removeprefix("fetch_").removesuffix("_addresses")
        for name in vars(blacklist_refresh_service)
        if name.startswith("fetch_") and name.endswith("_addresses")
    }


def registry_sources() -> set[str]:
    register_services(external_api_clients)
    groups = {
        "ioc_lookup": get_all_services(),
        "domain_finder": _domain_finder_providers(),
        "ru_business_check": AVAILABLE_SOURCES,
        "registry_dump": {job.source for job in _dump_jobs()},
        "address_blacklist": _blacklist_feeds(),
        "newsfeed": {feed["name"] for feed in DEFAULT_NEWSFEEDS},
        "dork_engine": dork_query_service._ENGINES,
        "phone_search": {checker.__name__.rsplit(".", 1)[-1] for checker in CHECKERS},
    }
    return {f"{namespace}:{name}" for namespace, names in groups.items() for name in names}


def _file_source_ids() -> set[str]:
    """Concrete (non-`<namespace>:*`) source ids named by FILE_SOURCES."""
    return {
        sid for sids in coverage_map.FILE_SOURCES.values() for sid in sids if not sid.endswith(":*")
    }


def test_every_registry_source_has_a_canary_or_an_exempt_reason():
    missing = sorted(registry_sources() - COVERAGE.keys())
    assert not missing, (
        f"add a canary or an Exempt reason for: {missing} in tests/canary/coverage_map.py"
    )


def test_every_one_off_source_is_mapped():
    one_off = _file_source_ids() | coverage_map.LIBRARY_SOURCES.keys()
    missing = sorted(one_off - COVERAGE.keys())
    assert not missing, (
        f"add a canary or an Exempt reason for: {missing} in tests/canary/coverage_map.py"
    )


def test_no_stale_coverage_entries():
    known = registry_sources() | _file_source_ids() | coverage_map.LIBRARY_SOURCES.keys()
    stale = sorted(COVERAGE.keys() - known)
    assert not stale, f"coverage_map.COVERAGE lists sources that no longer exist: {stale}"


def test_covered_entries_name_existing_canary_tests():
    broken = []
    for sid, entry in COVERAGE.items():
        if not isinstance(entry, Covered):
            continue
        module_name, _, test_name = entry.test.partition("::")
        module = importlib.import_module(f"tests.canary.{module_name}")
        if not test_name.startswith("test_") or not callable(getattr(module, test_name, None)):
            broken.append(f"{sid} -> {entry.test}")
    assert not broken, f"Covered entries point at missing canary tests: {broken}"


def test_exempt_reasons_are_from_the_fixed_vocabulary():
    bad = {
        sid: entry.reason
        for sid, entry in COVERAGE.items()
        if isinstance(entry, Exempt) and entry.reason not in EXEMPT_REASONS
    }
    assert not bad, f"unknown Exempt reasons (pick one of {sorted(EXEMPT_REASONS)}): {bad}"


def test_every_fixed_host_file_maps_onto_sources():
    mapped = coverage_map.FILE_SOURCES.keys() | coverage_map.FILE_EXEMPT.keys()
    unmapped = sorted(ALLOWLISTED_FIXED_HOST_FILES - mapped)
    assert not unmapped, (
        f"fixed-host client file(s) {unmapped} have no FILE_SOURCES/FILE_EXEMPT entry in "
        "tests/canary/coverage_map.py - name the sources they reach and give each a canary "
        "or an Exempt reason"
    )
    stale = sorted(mapped - ALLOWLISTED_FIXED_HOST_FILES)
    assert not stale, f"coverage_map file entries not in the SSRF allowlist any more: {stale}"


def test_file_sources_resolve_to_coverage_entries():
    dangling = sorted(
        f"{path} -> {sid}"
        for path, sids in coverage_map.FILE_SOURCES.items()
        for sid in sids
        if not any(fnmatch(key, sid) for key in COVERAGE)
    )
    assert not dangling, f"FILE_SOURCES names sources with no COVERAGE entry: {dangling}"


def test_library_sources_still_exist():
    missing = sorted(
        f"{sid} -> {module}"
        for sid, module in coverage_map.LIBRARY_SOURCES.items()
        if importlib.util.find_spec(module) is None
    )
    assert not missing, f"LIBRARY_SOURCES anchors no longer exist: {missing}"


def test_importing_the_canary_modules_makes_no_network_calls():
    # A fresh interpreter, so module-level code actually runs rather than hitting sys.modules.
    modules = sorted(f"tests.canary.{p.stem}" for p in CANARY_DIR.glob("*.py"))
    script = (
        "import socket\n"
        "def _blocked(*a, **k):\n"
        "    raise AssertionError(f'network call during import: {a!r}')\n"
        "socket.socket.connect = _blocked\n"
        "socket.socket.connect_ex = _blocked\n"
        "socket.getaddrinfo = _blocked\n"
        "socket.create_connection = _blocked\n"
        "import importlib\n"
        f"for name in {modules!r}:\n"
        "    importlib.import_module(name)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
