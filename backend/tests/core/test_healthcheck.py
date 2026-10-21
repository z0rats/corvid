"""`/api/healthcheck/*` drives the compose healthchecks and the Settings ->
About status panel: the status codes matter (503 = container unhealthy)."""

import shutil
import time
from collections import namedtuple
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import dependencies, healthcheck
from app.core.dependencies import get_database_health, get_disk_space_health
from tests.conftest import run

DiskUsage = namedtuple("DiskUsage", "total used free")
GB = 1024**3


@pytest.fixture
def make_client():
    def _make(db_status="healthy", disk_status="healthy", startup_time=None):
        app = FastAPI()
        app.include_router(healthcheck.router)
        app.state.startup_time = startup_time
        app.dependency_overrides[get_database_health] = lambda: {"status": db_status}
        app.dependency_overrides[get_disk_space_health] = lambda: {"status": disk_status}
        return TestClient(app)

    return _make


class TestEndpoints:
    def test_basic_ok(self, make_client):
        r = make_client(startup_time=time.time() - 65).get("/api/healthcheck")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["uptime"] == "1m 5s"

    def test_basic_unhealthy_db_is_503(self, make_client):
        r = make_client(db_status="unhealthy").get("/api/healthcheck")
        assert r.status_code == 503
        assert r.json()["status"] == "unhealthy"
        assert r.json()["uptime"] == "starting"

    @pytest.mark.parametrize(
        ("db", "disk", "code", "overall"),
        [
            ("healthy", "healthy", 200, "healthy"),
            ("healthy", "unknown", 200, "healthy"),
            ("healthy", "low", 503, "degraded"),
            ("unhealthy", "healthy", 503, "unhealthy"),
            ("unhealthy", "low", 503, "unhealthy"),
        ],
    )
    def test_detailed_status_matrix(self, make_client, db, disk, code, overall):
        r = make_client(db_status=db, disk_status=disk).get("/api/healthcheck/detailed")
        assert r.status_code == code
        body = r.json()
        assert body["status"] == overall
        assert set(body["services"]) == {"database", "disk", "api"}

    def test_readiness(self, make_client):
        assert make_client().get("/api/healthcheck/ready").json()["ready"] is True
        r = make_client(db_status="unhealthy").get("/api/healthcheck/ready")
        assert r.status_code == 503
        assert r.json() == {"ready": False, "reason": "Database not available"}

    def test_liveness_ignores_dependencies(self, make_client):
        r = make_client(db_status="unhealthy").get("/api/healthcheck/live")
        assert r.status_code == 200
        assert r.json()["alive"] is True

    def test_latest_release(self, make_client, monkeypatch):
        async def fake():
            return "1.2.3"

        monkeypatch.setattr(healthcheck, "get_latest_release_version", fake)
        assert make_client().get("/api/healthcheck/latest-release").json() == {
            "latest_version": "1.2.3"
        }


@pytest.mark.parametrize(
    ("elapsed", "expected"),
    [(0, "0s"), (59, "59s"), (3600, "1h 0s"), (90061, "1d 1h 1m 1s"), (86400 * 3 + 5, "3d 5s")],
)
def test_format_uptime(monkeypatch, elapsed, expected):
    monkeypatch.setattr(healthcheck.time, "time", lambda: 1_000_000.0)
    assert healthcheck._format_uptime(1_000_000.0 - elapsed) == expected


def test_overall_status_missing_database_is_unhealthy():
    assert healthcheck.determine_overall_status({}) == "unhealthy"


class TestHealthDependencies:
    def test_database_health_ok(self, monkeypatch):
        @asynccontextmanager
        async def session():
            class S:
                async def execute(self, stmt):
                    return None

            yield S()

        monkeypatch.setattr(dependencies, "managed_session", session)
        health = run(get_database_health())
        assert health["status"] == "healthy"
        assert health["connection"] == "active"
        assert health["database_type"]

    def test_database_health_failure(self, monkeypatch):
        @asynccontextmanager
        async def session():
            raise RuntimeError("disk I/O error")
            yield  # pragma: no cover

        monkeypatch.setattr(dependencies, "managed_session", session)
        health = run(get_database_health())
        assert health["status"] == "unhealthy"
        assert health["connection"] == "failed"

    def test_disk_low_vs_healthy(self, monkeypatch):
        settings = dependencies.get_settings()
        threshold = settings.low_disk_space_threshold_bytes
        monkeypatch.setattr(shutil, "disk_usage", lambda p: DiskUsage(100 * GB, 0, threshold - 1))
        assert get_disk_space_health(settings)["status"] == "low"
        monkeypatch.setattr(shutil, "disk_usage", lambda p: DiskUsage(100 * GB, 0, threshold))
        out = get_disk_space_health(settings)
        assert out["status"] == "healthy"
        assert out["total_gb"] == "100.00"

    def test_disk_error_is_unknown_not_crash(self, monkeypatch):
        def boom(p):
            raise FileNotFoundError("no data dir")

        monkeypatch.setattr(shutil, "disk_usage", boom)
        assert get_disk_space_health(dependencies.get_settings())["status"] == "unknown"
