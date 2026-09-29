"""Exercises `cli_tool_version.py`, the shared "-version"-flag-parsing helper for
CLI tools that aren't a pip package (subfinder_service.py, host_probe_service.py)."""

import subprocess

from app.core.utils import cli_tool_version
from app.core.utils.cli_tool_version import get_cli_tool_version, is_binary_available


def test_is_binary_available_reflects_shutil_which(monkeypatch):
    monkeypatch.setattr(cli_tool_version.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert is_binary_available("subfinder") is True

    monkeypatch.setattr(cli_tool_version.shutil, "which", lambda name: None)
    assert is_binary_available("subfinder") is False


def test_get_cli_tool_version_returns_none_when_not_installed(monkeypatch):
    monkeypatch.setattr(cli_tool_version, "is_binary_available", lambda name: False)

    assert get_cli_tool_version("subfinder") is None


def test_get_cli_tool_version_parses_default_regex(monkeypatch):
    monkeypatch.setattr(cli_tool_version, "is_binary_available", lambda name: True)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="Current Version: v1.12.0\n", stderr=""
        )

    monkeypatch.setattr(cli_tool_version.subprocess, "run", fake_run)

    assert get_cli_tool_version("httpx") == "v1.12.0"


def test_get_cli_tool_version_searches_stderr_too(monkeypatch):
    monkeypatch.setattr(cli_tool_version, "is_binary_available", lambda name: True)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="", stderr="Current Version: v2.16.0\n"
        )

    monkeypatch.setattr(cli_tool_version.subprocess, "run", fake_run)

    assert get_cli_tool_version("subfinder") == "v2.16.0"


def test_get_cli_tool_version_returns_none_when_unparseable(monkeypatch):
    monkeypatch.setattr(cli_tool_version, "is_binary_available", lambda name: True)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="garbage", stderr="")

    monkeypatch.setattr(cli_tool_version.subprocess, "run", fake_run)

    assert get_cli_tool_version("subfinder") is None


def test_get_cli_tool_version_returns_none_on_subprocess_error(monkeypatch):
    monkeypatch.setattr(cli_tool_version, "is_binary_available", lambda name: True)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="subfinder", timeout=10)

    monkeypatch.setattr(cli_tool_version.subprocess, "run", fake_run)

    assert get_cli_tool_version("subfinder") is None


def test_get_cli_tool_version_passes_custom_args_and_regex(monkeypatch):
    import re

    monkeypatch.setattr(cli_tool_version, "is_binary_available", lambda name: True)
    captured_args = []

    def fake_run(args, **kwargs):
        captured_args.append(args)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ver=9.9.9", stderr="")

    monkeypatch.setattr(cli_tool_version.subprocess, "run", fake_run)

    result = get_cli_tool_version(
        "exampletool", version_args=("-ver",), version_regex=re.compile(r"ver=(\S+)")
    )

    assert result == "9.9.9"
    assert captured_args == [["exampletool", "-ver"]]
