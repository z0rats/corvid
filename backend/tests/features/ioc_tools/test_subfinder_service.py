"""asyncio.create_subprocess_exec is monkeypatched directly (rather than shelling
out to a real subfinder binary) so these tests focus on perform_subfinder_lookup's
own logic: JSONL parsing, per-host source aggregation/dedup, and error handling
(missing binary, non-zero exit, timeout). get_subfinder_version just delegates to
`core/utils/cli_tool_version.py`'s get_cli_tool_version, tested generically in
test_cli_tool_version.py - here we only check it's wired to the right binary name."""

import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import SubfinderSubdomainsRequest
from app.features.ioc_tools.domain_finder.service import subfinder_service
from app.features.ioc_tools.domain_finder.service.subfinder_service import (
    get_subfinder_version,
    perform_subfinder_lookup,
)


def _run(coro):
    return asyncio.run(coro)


class _FakeProcess:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0, hang=False):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self._hang = hang
        self.killed = False
        self.waited = False

    async def communicate(self):
        if self._hang:
            await asyncio.sleep(999)
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True

    async def wait(self):
        self.waited = True
        return self.returncode


def _patch_subprocess(monkeypatch, process: _FakeProcess, *, available: bool = True):
    async def fake_create_subprocess_exec(*args, **kwargs):
        return process

    monkeypatch.setattr(subfinder_service, "is_subfinder_available", lambda: available)
    monkeypatch.setattr(
        subfinder_service.asyncio, "create_subprocess_exec", fake_create_subprocess_exec
    )


def test_parses_jsonl_and_aggregates_sources_per_host(monkeypatch):
    stdout = (
        b'{"host":"www.example.com","input":"example.com","source":"crtsh"}\n'
        b'{"host":"www.example.com","input":"example.com","source":"github"}\n'
        b'{"host":"www.example.com","input":"example.com","source":"crtsh"}\n'
        b'{"host":"mail.example.com","input":"example.com","source":"hackertarget"}\n'
    )
    _patch_subprocess(monkeypatch, _FakeProcess(stdout=stdout, returncode=0))

    result = _run(perform_subfinder_lookup(SubfinderSubdomainsRequest(domain="example.com")))

    assert result.subdomains == ["mail.example.com", "www.example.com"]
    assert result.total_records == 2
    by_host = {r.hostname: r.sources for r in result.records}
    assert by_host["www.example.com"] == ["crtsh", "github"]
    assert by_host["mail.example.com"] == ["hackertarget"]


def test_skips_unparseable_lines_and_entries_missing_host(monkeypatch):
    stdout = (
        b"not json at all\n"
        b'{"input":"example.com","source":"crtsh"}\n'
        b'{"host":"api.example.com","input":"example.com","source":"crtsh"}\n'
        b"\n"
    )
    _patch_subprocess(monkeypatch, _FakeProcess(stdout=stdout, returncode=0))

    result = _run(perform_subfinder_lookup(SubfinderSubdomainsRequest(domain="example.com")))

    assert result.subdomains == ["api.example.com"]
    assert result.total_records == 1


def test_raises_503_when_binary_not_installed(monkeypatch):
    _patch_subprocess(monkeypatch, _FakeProcess(), available=False)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_subfinder_lookup(SubfinderSubdomainsRequest(domain="example.com")))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "SUBFINDER_NOT_INSTALLED"


def test_raises_502_on_nonzero_exit(monkeypatch):
    _patch_subprocess(
        monkeypatch, _FakeProcess(stderr=b"could not resolve provider config", returncode=1)
    )

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_subfinder_lookup(SubfinderSubdomainsRequest(domain="example.com")))

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "SUBFINDER_EXECUTION_ERROR"
    assert "could not resolve provider config" in exc_info.value.detail


def test_raises_504_and_kills_process_on_timeout(monkeypatch):
    process = _FakeProcess(hang=True)
    _patch_subprocess(monkeypatch, process)
    monkeypatch.setattr(subfinder_service, "PROCESS_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_subfinder_lookup(SubfinderSubdomainsRequest(domain="example.com")))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "SUBFINDER_TIMEOUT"
    assert process.killed is True
    assert process.waited is True


def test_subfinder_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        SubfinderSubdomainsRequest(domain="example-*")


class TestGetSubfinderVersion:
    def setup_method(self):
        get_subfinder_version.cache_clear()

    def teardown_method(self):
        get_subfinder_version.cache_clear()

    def test_delegates_to_cli_tool_version_for_the_right_binary(self, monkeypatch):
        captured = []
        monkeypatch.setattr(
            subfinder_service,
            "get_cli_tool_version",
            lambda binary_name: captured.append(binary_name) or "v2.16.0",
        )

        assert get_subfinder_version() == "v2.16.0"
        assert captured == ["subfinder"]
