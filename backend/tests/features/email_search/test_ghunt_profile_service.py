"""run_ghunt_profile is exercised against a monkeypatched asyncio.create_subprocess_exec, the
same style as test_amass_service.py's TestRunSubs. The success-path fixture
(fixtures/ghunt_email_output.json) is code-derived from the pinned GHunt 2.3.4 source, not a
live capture - see docs/architecture/ghunt.md for why, and for the exit-code mapping this
exercises.
"""

import asyncio
import base64
import json
import os
import stat
from pathlib import Path

import pytest

from app.core.exceptions import AppHTTPException
from app.features.email_search.service import ghunt_profile_service as svc

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ghunt_email_output.json"


def _run(coro):
    return asyncio.run(coro)


def _valid_session_value() -> str:
    data = {
        "cookies": {"SID": "abc"},
        "osids": {"1": "osid"},
        "android": {"master_token": "token", "authorization_tokens": {}},
    }
    return base64.b64encode(json.dumps(data).encode()).decode()


VALID_SESSION_VALUE = _valid_session_value()


class _FakeApikey:
    def __init__(self, key: str, is_active: bool = True):
        self.key = key
        self.is_active = is_active

    def is_usable(self) -> bool:
        return self.is_active and bool(self.key and self.key.strip())


class _FakeProcess:
    def __init__(self, returncode: int = 0, stderr: bytes = b"", hang: bool = False):
        self.returncode = None if hang else returncode
        self._stderr = stderr
        self._hang = hang
        self.killed = False
        self.write_output_path: str | None = None
        self.output_content: str | None = None

    async def communicate(self):
        if self._hang:
            await asyncio.sleep(999)
        if self.write_output_path and self.output_content is not None:
            Path(self.write_output_path).write_text(self.output_content, encoding="utf-8")
        return b"", self._stderr

    def kill(self):
        self.killed = True
        self._hang = False
        self.returncode = -9

    async def wait(self):
        return self.returncode


def _patch_apikey(monkeypatch, apikey):
    async def fake_get_apikey(db, name):
        assert name == "ghunt_session"
        return apikey

    monkeypatch.setattr(svc, "get_apikey", fake_get_apikey)


def _patch_subprocess(monkeypatch, process: _FakeProcess, *, write_fixture: bool = False):
    captured = {}

    async def fake_create_subprocess_exec(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        if write_fixture:
            process.write_output_path = args[4]  # GHUNT_BIN, "email", email, "--json", <path>
            process.output_content = FIXTURE_PATH.read_text(encoding="utf-8")
        return process

    monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    return captured


class TestRunGhuntProfileSessionGating:
    def test_missing_session_raises_409(self, monkeypatch):
        _patch_apikey(monkeypatch, None)

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "GHUNT_SESSION_MISSING"

    def test_inactive_session_raises_409(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE, is_active=False))

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.error_code == "GHUNT_SESSION_MISSING"

    def test_structurally_invalid_session_raises_409_invalid(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey("not-a-valid-session", is_active=True))

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "GHUNT_SESSION_INVALID"


class TestRunGhuntProfileSubprocess:
    def test_success_parses_the_fixture(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        _patch_subprocess(monkeypatch, _FakeProcess(returncode=0), write_fixture=True)

        result = _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert result.gaia_id == "123456789012345678901"
        assert result.email == "target@gmail.com"
        assert result.profile_photo.url == "https://example.com/photo.jpg"
        assert result.profile_photo.is_default is False
        assert result.cover_photo.is_default is True
        assert result.user_types == ["GOOGLE_USER"]
        assert result.activated_services == ["Gmail", "Photos"]
        assert result.maps == {
            "photos": None,
            "reviews": None,
            "stats": {"Reviews": 3, "Ratings": 5, "Photos": 12},
        }
        assert result.play_games is None
        assert result.last_profile_edit is not None
        assert result.last_profile_edit.year == 2024

    def test_zero_exit_with_no_output_file_is_not_found(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        _patch_subprocess(monkeypatch, _FakeProcess(returncode=0), write_fixture=False)

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "GHUNT_NOT_FOUND"

    def test_nonzero_exit_with_session_marker_is_session_expired(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        stderr = b"ghunt.errors.GHuntInvalidSession: Please generate a new session"
        _patch_subprocess(monkeypatch, _FakeProcess(returncode=1, stderr=stderr))

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.status_code == 409
        assert exc_info.value.error_code == "GHUNT_SESSION_EXPIRED"

    def test_nonzero_exit_without_session_marker_is_execution_error(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        stderr = b"Traceback (most recent call last):\nRuntimeError: something else broke"
        _patch_subprocess(monkeypatch, _FakeProcess(returncode=1, stderr=stderr))

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.status_code == 502
        assert exc_info.value.error_code == "GHUNT_EXECUTION_ERROR"
        assert "RuntimeError" in exc_info.value.detail

    def test_stderr_is_truncated_in_the_error_detail(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        stderr = b"x" * 5000
        _patch_subprocess(monkeypatch, _FakeProcess(returncode=1, stderr=stderr))

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert len(exc_info.value.detail) <= 500

    def test_timeout_kills_the_process_and_raises_504(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        process = _FakeProcess(hang=True)
        _patch_subprocess(monkeypatch, process)
        monkeypatch.setattr(svc, "TIMEOUT_SECONDS", 0.01)

        with pytest.raises(AppHTTPException) as exc_info:
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        assert exc_info.value.status_code == 504
        assert exc_info.value.error_code == "GHUNT_TIMEOUT"
        assert process.killed is True

    def test_temp_home_is_removed_after_success(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        captured = _patch_subprocess(monkeypatch, _FakeProcess(returncode=0), write_fixture=True)

        _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        home = captured["kwargs"]["env"]["HOME"]
        assert not os.path.exists(home)

    def test_temp_home_is_removed_even_on_execution_error(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        captured = _patch_subprocess(monkeypatch, _FakeProcess(returncode=1, stderr=b"boom"))

        with pytest.raises(AppHTTPException):
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        home = captured["kwargs"]["env"]["HOME"]
        assert not os.path.exists(home)

    def test_child_process_gets_an_isolated_home_and_minimal_env(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        captured = _patch_subprocess(monkeypatch, _FakeProcess(returncode=0), write_fixture=True)

        _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))

        env = captured["kwargs"]["env"]
        assert set(env.keys()) == {"HOME", "PATH"}
        assert env["HOME"] != os.environ.get("HOME")

    def test_creds_file_is_written_with_restrictive_permissions(self, monkeypatch):
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))
        written_paths = []

        real_write_text = Path.write_text

        def spying_write_text(self, *args, **kwargs):
            written_paths.append(self)
            return real_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", spying_write_text)

        async def fake_create_subprocess_exec(*args, **kwargs):
            creds_path = [p for p in written_paths if p.name == "creds.m"][0]
            mode = stat.S_IMODE(os.stat(creds_path).st_mode)
            assert mode == 0o600
            return _FakeProcess(returncode=0)

        monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

        with pytest.raises(AppHTTPException):
            # No output file written by this fake process -> 404, but the permission
            # assertion above already ran by the time we get there.
            _run(svc.run_ghunt_profile(db=None, email="target@gmail.com"))


class TestGetGhuntVersion:
    def setup_method(self):
        svc.get_ghunt_version.cache_clear()

    def teardown_method(self):
        svc.get_ghunt_version.cache_clear()

    def test_uses_a_cheap_help_call_and_the_ghunt_version_regex(self, monkeypatch):
        captured = {}

        def fake_get_cli_tool_version(binary_name, **kwargs):
            captured["binary_name"] = binary_name
            captured.update(kwargs)
            return "2.3.4"

        monkeypatch.setattr(svc, "get_cli_tool_version", fake_get_cli_tool_version)

        assert svc.get_ghunt_version() == "2.3.4"
        assert captured["binary_name"] == svc.GHUNT_BIN
        assert captured["version_args"] == ("--help",)
        match = captured["version_regex"].search("> GHunt 2.3.4 (Spider Edition) <")
        assert match.group(1) == "2.3.4"

    def test_is_cached(self, monkeypatch):
        calls = []

        def fake_get_cli_tool_version(binary_name, **kwargs):
            calls.append(1)
            return "2.3.4"

        monkeypatch.setattr(svc, "get_cli_tool_version", fake_get_cli_tool_version)

        svc.get_ghunt_version()
        svc.get_ghunt_version()

        assert len(calls) == 1


class TestGetGhuntHealth:
    def test_reports_installed_version_and_session_state(self, monkeypatch):
        svc.get_ghunt_version.cache_clear()
        monkeypatch.setattr(svc, "get_cli_tool_version", lambda *a, **k: "2.3.4")

        async def fake_fetch_latest(package_name):
            assert package_name == "ghunt"
            return "2.3.5"

        monkeypatch.setattr(svc, "fetch_latest_pypi_version", fake_fetch_latest)
        _patch_apikey(monkeypatch, _FakeApikey(VALID_SESSION_VALUE))

        result = _run(svc.get_ghunt_health(db=None))

        assert result.installed is True
        assert result.version == "2.3.4"
        assert result.latest_version == "2.3.5"
        assert result.session_configured is True
        svc.get_ghunt_version.cache_clear()

    def test_session_not_configured_when_missing(self, monkeypatch):
        svc.get_ghunt_version.cache_clear()
        monkeypatch.setattr(svc, "get_cli_tool_version", lambda *a, **k: None)

        async def fake_fetch_latest(package_name):
            return None

        monkeypatch.setattr(svc, "fetch_latest_pypi_version", fake_fetch_latest)
        _patch_apikey(monkeypatch, None)

        result = _run(svc.get_ghunt_health(db=None))

        assert result.installed is False
        assert result.session_configured is False
        svc.get_ghunt_version.cache_clear()
