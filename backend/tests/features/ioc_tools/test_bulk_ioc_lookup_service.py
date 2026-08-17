import asyncio
from types import SimpleNamespace

from app.features.ioc_tools.ioc_lookup.bulk_lookup.service import bulk_ioc_lookup_service as svc
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import (
    LookupResult,
    LookupStatus,
    ServiceInfo,
)


def _run(coro):
    return asyncio.run(coro)


def _service_config(key="virustotal", supported=("ip",)):
    return SimpleNamespace(supported_ioc_types=list(supported))


class TestRunSingleLookupWithRateLimit:
    def test_returns_error_for_unconfigured_service(self, monkeypatch):
        monkeypatch.setattr(svc, "get_service", lambda name: None)

        result = _run(
            svc.run_single_lookup_with_rate_limit(
                "nonexistent",
                "1.2.3.4",
                "ip",
                db=None,
                semaphore=asyncio.Semaphore(1),
            )
        )

        assert result["status"] == LookupStatus.ERROR.value
        assert "not configured" in result["error"]

    def test_returns_error_for_unsupported_ioc_type(self, monkeypatch):
        monkeypatch.setattr(svc, "get_service", lambda name: _service_config(supported=("ip",)))

        result = _run(
            svc.run_single_lookup_with_rate_limit(
                "virustotal",
                "example.com",
                "domain",
                db=None,
                semaphore=asyncio.Semaphore(1),
            )
        )

        assert result["status"] == LookupStatus.ERROR.value
        assert "doesn't support domain" in result["error"]

    def test_returns_success_data_on_successful_lookup(self, monkeypatch):
        monkeypatch.setattr(svc, "get_service", lambda name: _service_config())

        async def fake_lookup_ioc(service_name, ioc, ioc_type, db):
            return LookupResult(
                ioc=ioc, service=service_name, status=LookupStatus.SUCCESS, data={"score": 1}
            )

        monkeypatch.setattr(svc, "lookup_ioc", fake_lookup_ioc)

        result = _run(
            svc.run_single_lookup_with_rate_limit(
                "virustotal",
                "1.2.3.4",
                "ip",
                db=None,
                semaphore=asyncio.Semaphore(1),
            )
        )

        assert result == {"status": LookupStatus.SUCCESS.value, "data": {"score": 1}}

    def test_passes_through_non_success_status_and_error(self, monkeypatch):
        monkeypatch.setattr(svc, "get_service", lambda name: _service_config())

        async def fake_lookup_ioc(service_name, ioc, ioc_type, db):
            return LookupResult(
                ioc=ioc,
                service=service_name,
                status=LookupStatus.UNAUTHORIZED,
                error="no key configured",
            )

        monkeypatch.setattr(svc, "lookup_ioc", fake_lookup_ioc)

        result = _run(
            svc.run_single_lookup_with_rate_limit(
                "virustotal",
                "1.2.3.4",
                "ip",
                db=None,
                semaphore=asyncio.Semaphore(1),
            )
        )

        assert result == {"status": LookupStatus.UNAUTHORIZED.value, "error": "no key configured"}

    def test_unexpected_exception_is_caught_and_returned_as_error(self, monkeypatch):
        monkeypatch.setattr(svc, "get_service", lambda name: _service_config())

        async def fake_lookup_ioc(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(svc, "lookup_ioc", fake_lookup_ioc)

        result = _run(
            svc.run_single_lookup_with_rate_limit(
                "virustotal",
                "1.2.3.4",
                "ip",
                db=None,
                semaphore=asyncio.Semaphore(1),
            )
        )

        assert result["status"] == LookupStatus.ERROR.value
        assert "boom" in result["error"]


class TestProcessBulkLookupsWithRateLimiting:
    async def _collect(self, gen):
        return [item async for item in gen]

    def test_yields_system_error_when_no_services_available(self, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VT",
                    supported_ioc_types=["ip"],
                    is_configured=False,
                    is_bulk_enabled=False,
                )
            ]

        monkeypatch.setattr(svc, "get_all_service_configs", fake_get_all_service_configs)

        results = _run(
            self._collect(
                svc.process_bulk_lookups_with_rate_limiting(
                    ["1.2.3.4"],
                    ["virustotal"],
                    db=None,
                )
            )
        )

        assert len(results) == 1
        assert results[0]["status"] == LookupStatus.ERROR.value
        assert results[0]["service"] == "system"

    def test_yields_error_for_unknown_ioc_type(self, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VT",
                    supported_ioc_types=["ip"],
                    is_configured=True,
                    is_bulk_enabled=True,
                )
            ]

        monkeypatch.setattr(svc, "get_all_service_configs", fake_get_all_service_configs)

        results = _run(
            self._collect(
                svc.process_bulk_lookups_with_rate_limiting(
                    ["not-a-real-ioc!!!"],
                    ["virustotal"],
                    db=None,
                    max_concurrent_requests=2,
                )
            )
        )

        assert any(
            r["status"] == LookupStatus.ERROR.value and r["error"] == "Unknown IOC type"
            for r in results
        )

    def test_yields_success_result_for_supported_ioc(self, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VT",
                    supported_ioc_types=["IPv4"],
                    is_configured=True,
                    is_bulk_enabled=True,
                )
            ]

        monkeypatch.setattr(svc, "get_all_service_configs", fake_get_all_service_configs)
        monkeypatch.setattr(svc, "get_service", lambda name: _service_config(supported=("IPv4",)))

        async def fake_lookup_ioc(service_name, ioc, ioc_type, db):
            return LookupResult(
                ioc=ioc, service=service_name, status=LookupStatus.SUCCESS, data={"ok": True}
            )

        monkeypatch.setattr(svc, "lookup_ioc", fake_lookup_ioc)

        results = _run(
            self._collect(
                svc.process_bulk_lookups_with_rate_limiting(
                    ["1.2.3.4"],
                    ["virustotal"],
                    db=None,
                    max_concurrent_requests=2,
                )
            )
        )

        assert results == [
            {
                "ioc": "1.2.3.4",
                "service": "virustotal",
                "status": LookupStatus.SUCCESS.value,
                "data": {"ok": True},
            }
        ]

    def test_skips_service_that_does_not_support_the_ioc_type(self, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VT",
                    supported_ioc_types=["IPv4", "Domain"],
                    is_configured=True,
                    is_bulk_enabled=True,
                )
            ]

        monkeypatch.setattr(svc, "get_all_service_configs", fake_get_all_service_configs)
        # Registered service only supports "Domain", not the "IPv4" IOC being queried.
        monkeypatch.setattr(svc, "get_service", lambda name: _service_config(supported=("Domain",)))

        results = _run(
            self._collect(
                svc.process_bulk_lookups_with_rate_limiting(
                    ["1.2.3.4"],
                    ["virustotal"],
                    db=None,
                    max_concurrent_requests=2,
                )
            )
        )

        assert results == []
