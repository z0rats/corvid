"""The reviewed module manifest and the installed user-scanner package must agree.

user-scanner modules each ask one service "does this address have an account?", and some do it
through a password-reset or signup endpoint, which emails the *target*. Only manifest-approved
modules ever run (`get_runnable_modules`), so a module that appears in a package upgrade stays off
until someone reads it and adds it here: that is what the first test enforces.
"""

import json

import pytest

from app.features.email_search.config import user_scanner_config as cfg


def _installed_stems():
    pytest.importorskip("user_scanner")
    from user_scanner.core.helpers import load_categories, load_modules

    return {
        module.__name__.split(".")[-1]: (category, module)
        for category, path in load_categories(is_email=True).items()
        for module in load_modules(path)
    }


class TestManifestShape:
    def test_every_entry_has_a_category_and_a_decision_and_a_blocked_one_says_why(self):
        for stem, entry in cfg.load_manifest().items():
            assert isinstance(entry["run"], bool), stem
            assert entry["category"], stem
            assert entry["run"] or entry.get("reason"), f"{stem} is blocked without a reason"

    def test_adult_modules_are_never_runnable(self):
        runnable_adult = [
            s for s, e in cfg.load_manifest().items() if e["category"] == "adult" and e["run"]
        ]
        assert runnable_adult == []

    def test_known_notifying_modules_are_blocked(self):
        manifest = cfg.load_manifest()
        for stem in ("anilist", "cv_ee", "netflix", "rubygems", "facebook", "medium"):
            assert manifest[stem]["run"] is False, stem

    def test_runnable_count_matches_the_manifest(self):
        assert cfg.runnable_module_count() == sum(e["run"] for e in cfg.load_manifest().values())
        assert cfg.runnable_module_count() > 100

    def test_the_manifest_file_is_valid_json_with_the_reviewed_version(self):
        raw = json.loads(cfg.MANIFEST_PATH.read_text())
        assert raw["package_version"] and raw["modules"]


class TestManifestMatchesTheInstalledPackage:
    def test_every_installed_module_has_been_reviewed(self):
        """Fails after a user-scanner upgrade adds a module: read what its request does (does it
        trigger a password-reset/OTP/verification email, or create an account?) and add it to the
        manifest with run=true, or run=false and a reason. Removed modules should be dropped too."""
        installed = set(_installed_stems())
        reviewed = set(cfg.load_manifest())

        assert sorted(installed - reviewed) == [], "new modules need review"
        assert sorted(reviewed - installed) == [], (
            "manifest lists modules the package no longer has"
        )

    def test_no_runnable_module_is_on_upstreams_own_loud_list(self):
        pytest.importorskip("user_scanner")
        from user_scanner.core.helpers import get_site_name, is_loud

        runnable = [
            stem
            for stem, (_, module) in _installed_stems().items()
            if cfg.load_manifest()[stem]["run"] and is_loud(get_site_name(module), is_email=True)
        ]
        assert runnable == []

    def test_manifest_categories_match_the_package_layout(self):
        wrong = [
            stem
            for stem, (category, _) in _installed_stems().items()
            if cfg.load_manifest()[stem]["category"] != category
        ]
        assert wrong == []

    def test_get_runnable_modules_returns_exactly_the_approved_ones(self):
        pytest.importorskip("user_scanner")
        names = {m.__name__.split(".")[-1] for m in cfg.get_runnable_modules()}
        assert names == {s for s, e in cfg.load_manifest().items() if e["run"]}

    def test_importing_the_engine_does_not_patch_httpx(self):
        """user_scanner's email orchestrator monkey-patches httpx clients process-wide; we only
        ever import the engine, and must never pull the orchestrator in."""
        pytest.importorskip("user_scanner")
        import importlib
        import sys

        import httpx

        before = httpx.AsyncClient.__init__
        importlib.import_module("user_scanner.core.engine")
        cfg.get_runnable_modules()

        assert httpx.AsyncClient.__init__ is before
        assert "user_scanner.core.email_orchestrator" not in sys.modules


class TestAvailability:
    def test_is_available_follows_the_package_metadata(self, monkeypatch):
        def missing(_name):
            raise cfg.importlib_metadata.PackageNotFoundError

        monkeypatch.setattr(cfg.importlib_metadata, "version", missing)

        assert cfg.is_available() is False

    def test_is_available_when_installed(self, monkeypatch):
        monkeypatch.setattr(cfg.importlib_metadata, "version", lambda _name: "1.5.2.1")

        assert cfg.is_available() is True
        assert cfg.get_installed_version() == "1.5.2.1"
