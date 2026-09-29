"""resolve_validated_ip and asyncio.create_subprocess_exec are monkeypatched
directly (rather than exercising real DNS/a real httpx binary) so these tests
focus on perform_host_probe's own logic: the SSRF pre-check ahead of the
subprocess, JSONL parsing into HostProbeResult, filtering failed/incomplete
entries, and error handling (invalid host, missing binary, non-zero exit,
timeout). get_httpx_version just delegates to core/utils/cli_tool_version.py,
tested generically in test_cli_tool_version.py."""

import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.core.security.ssrf_guard import SSRFValidationError
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import HostProbeRequest
from app.features.ioc_tools.domain_finder.service import host_probe_service
from app.features.ioc_tools.domain_finder.service.host_probe_service import (
    get_httpx_version,
    perform_host_probe,
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


def _patch(monkeypatch, process: _FakeProcess, *, available: bool = True, resolve_exc=None):
    async def fake_create_subprocess_exec(*args, **kwargs):
        return process

    def fake_resolve_validated_ip(domain, **kwargs):
        if resolve_exc:
            raise resolve_exc
        return "93.184.216.34"

    monkeypatch.setattr(host_probe_service, "resolve_validated_ip", fake_resolve_validated_ip)
    monkeypatch.setattr(host_probe_service, "is_httpx_available", lambda: available)
    monkeypatch.setattr(
        host_probe_service.asyncio, "create_subprocess_exec", fake_create_subprocess_exec
    )


def test_parses_live_hosts_from_jsonl(monkeypatch):
    stdout = (
        b'{"url":"https://example.com","final_url":"https://example.com/","scheme":"https",'
        b'"status_code":200,"title":"Example Domain","webserver":"ECS","content_type":"text/html",'
        b'"content_length":1256,"tech":["nginx"],"favicon":"12345","chain_status_codes":[200]}\n'
        b'{"url":"http://example.com","scheme":"http","status_code":301}\n'
    )
    _patch(monkeypatch, _FakeProcess(stdout=stdout, returncode=0))

    result = _run(perform_host_probe(HostProbeRequest(domain="example.com")))

    assert result.reachable is True
    assert len(result.results) == 2
    https_result = next(r for r in result.results if r.scheme == "https")
    assert https_result.title == "Example Domain"
    assert https_result.technologies == ["nginx"]
    assert https_result.favicon_hash == "12345"
    http_result = next(r for r in result.results if r.scheme == "http")
    assert http_result.status_code == 301
    assert http_result.title is None


def test_skips_failed_and_incomplete_entries(monkeypatch):
    stdout = (
        b'{"url":"https://example.com","scheme":"https","status_code":200,"failed":true}\n'
        b'{"scheme":"https","status_code":200}\n'
        b"not json\n"
        b'{"url":"https://example.com","scheme":"https","status_code":200}\n'
    )
    _patch(monkeypatch, _FakeProcess(stdout=stdout, returncode=0))

    result = _run(perform_host_probe(HostProbeRequest(domain="example.com")))

    assert result.reachable is True
    assert len(result.results) == 1


def test_reachable_is_false_with_no_output(monkeypatch):
    _patch(monkeypatch, _FakeProcess(stdout=b"", returncode=0))

    result = _run(perform_host_probe(HostProbeRequest(domain="example.com")))

    assert result.reachable is False
    assert result.results == []


def test_raises_400_when_domain_resolves_to_private_ip(monkeypatch):
    _patch(
        monkeypatch,
        _FakeProcess(),
        resolve_exc=SSRFValidationError("resolves to a private address"),
    )

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_host_probe(HostProbeRequest(domain="internal.example")))

    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "HOST_PROBE_INVALID_HOST"


def test_ssrf_check_happens_before_spawning_the_subprocess(monkeypatch):
    """The subprocess factory should never be called when the SSRF pre-check fails."""
    calls = []

    async def fake_create_subprocess_exec(*args, **kwargs):
        calls.append(args)
        raise AssertionError("subprocess should not be spawned")

    def fake_resolve_validated_ip(domain, **kwargs):
        raise SSRFValidationError("resolves to a private address")

    monkeypatch.setattr(host_probe_service, "resolve_validated_ip", fake_resolve_validated_ip)
    monkeypatch.setattr(
        host_probe_service.asyncio, "create_subprocess_exec", fake_create_subprocess_exec
    )

    with pytest.raises(AppHTTPException):
        _run(perform_host_probe(HostProbeRequest(domain="internal.example")))

    assert calls == []


def test_raises_503_when_binary_not_installed(monkeypatch):
    _patch(monkeypatch, _FakeProcess(), available=False)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_host_probe(HostProbeRequest(domain="example.com")))

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "HOST_PROBE_NOT_INSTALLED"


def test_raises_502_on_nonzero_exit(monkeypatch):
    _patch(monkeypatch, _FakeProcess(stderr=b"invalid target", returncode=1))

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_host_probe(HostProbeRequest(domain="example.com")))

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "HOST_PROBE_EXECUTION_ERROR"
    assert "invalid target" in exc_info.value.detail


def test_raises_504_and_kills_process_on_timeout(monkeypatch):
    process = _FakeProcess(hang=True)
    _patch(monkeypatch, process)
    monkeypatch.setattr(host_probe_service, "PROCESS_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(perform_host_probe(HostProbeRequest(domain="example.com")))

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "HOST_PROBE_TIMEOUT"
    assert process.killed is True
    assert process.waited is True


def test_host_probe_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        HostProbeRequest(domain="example-*")


class TestGetHttpxVersion:
    def setup_method(self):
        get_httpx_version.cache_clear()

    def teardown_method(self):
        get_httpx_version.cache_clear()

    def test_delegates_to_cli_tool_version_for_the_right_binary(self, monkeypatch):
        captured = []
        monkeypatch.setattr(
            host_probe_service,
            "get_cli_tool_version",
            lambda binary_name: captured.append(binary_name) or "v1.12.0",
        )

        assert get_httpx_version() == "v1.12.0"
        assert captured == ["httpx-probe"]
