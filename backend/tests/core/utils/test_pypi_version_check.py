"""Exercises `pypi_version_check.py`, the single fetch+record+compute+orchestrate
module shared by every "check PyPI for a newer <vendored tool>" endpoint
(maigret/social-analyzer under username_search, mailcat-osint under email_search).

`fetch_latest_pypi_version` is tested against `httpx.MockTransport` (same pattern
as `test_crtsh_api_service.py`) so `raise_for_status()`/`response.json()` parsing
runs for real. `record_pypi_check`/`check_for_update` are tested against a real
sqlite-backed fake model carrying `PypiVersionCheckMixin` (same engine-fixture
pattern as `test_scan_crud.py`), rather than any of the three real *Config models,
since the whole point of the mixin is that it doesn't matter which one is used.
"""

import asyncio
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config.settings import settings
from app.core.database import Base, create_database_engine
from app.core.models.mixins import PypiVersionCheckMixin
from app.core.utils import pypi_version_check


class FakeToolConfig(Base, PypiVersionCheckMixin):
    """Minimal stand-in for a real `*Config` model, carrying only the mixin's columns."""

    __tablename__ = "test_pypi_version_check_fake_tool_config"

    id: Mapped[int] = mapped_column(primary_key=True)


def _run(coro):
    return asyncio.run(coro)


def _patch_transport(monkeypatch, handler):
    real_async_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)


@pytest.fixture
def engine(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "pypi_version_check.db"
    monkeypatch.setattr(settings.database, "url", f"sqlite:///{db_path}")
    eng = create_database_engine()
    yield eng
    _run(eng.dispose())


def _session_factory(engine):
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[FakeToolConfig.__table__])

    _run(_create_tables())
    return async_sessionmaker(engine, expire_on_commit=False)


class TestFetchLatestPypiVersion:
    def test_returns_version_on_success(self, monkeypatch):
        def handler(request):
            assert request.url.path == "/pypi/some-package/json"
            return httpx.Response(200, json={"info": {"version": "1.2.3"}})

        _patch_transport(monkeypatch, handler)

        result = _run(pypi_version_check.fetch_latest_pypi_version("some-package"))

        assert result == "1.2.3"

    def test_returns_none_on_network_error(self, monkeypatch):
        def handler(request):
            raise httpx.ConnectError("offline")

        _patch_transport(monkeypatch, handler)

        result = _run(pypi_version_check.fetch_latest_pypi_version("some-package"))

        assert result is None

    def test_returns_none_on_http_error_status(self, monkeypatch):
        _patch_transport(monkeypatch, lambda request: httpx.Response(404))

        result = _run(pypi_version_check.fetch_latest_pypi_version("some-package"))

        assert result is None

    def test_returns_none_on_unexpected_json_shape(self, monkeypatch):
        _patch_transport(
            monkeypatch, lambda request: httpx.Response(200, json={"unexpected": "shape"})
        )

        result = _run(pypi_version_check.fetch_latest_pypi_version("some-package"))

        assert result is None


class TestComputeUpdateAvailable:
    def test_none_when_never_checked(self):
        assert pypi_version_check.compute_update_available(None, "1.0.0") is None

    def test_true_when_latest_differs_from_installed(self):
        assert pypi_version_check.compute_update_available("2.0.0", "1.0.0") is True

    def test_false_when_latest_matches_installed(self):
        assert pypi_version_check.compute_update_available("1.0.0", "1.0.0") is False


class TestRecordPypiCheck:
    def test_sets_latest_version_and_checked_at(self, engine):
        session_factory = _session_factory(engine)

        async def _scenario():
            async with session_factory() as db:
                config = FakeToolConfig()
                db.add(config)
                await db.commit()
                config_id = config.id

            async with session_factory() as db:
                config = (
                    await db.execute(select(FakeToolConfig).where(FakeToolConfig.id == config_id))
                ).scalar_one()
                await pypi_version_check.record_pypi_check(db, config, "3.1.4")
                await db.commit()

            async with session_factory() as db:
                return (
                    await db.execute(select(FakeToolConfig).where(FakeToolConfig.id == config_id))
                ).scalar_one()

        row = _run(_scenario())
        assert row.latest_pypi_version == "3.1.4"
        assert row.pypi_checked_at is not None


class TestCheckForUpdate:
    def test_orchestrates_fetch_record_and_compute(self, engine, monkeypatch):
        async def fake_fetch(package_name, timeout_seconds=5.0):
            assert package_name == "some-package"
            return "9.9.9"

        monkeypatch.setattr(pypi_version_check, "fetch_latest_pypi_version", fake_fetch)
        session_factory = _session_factory(engine)

        async def _scenario():
            async with session_factory() as db:
                config = FakeToolConfig()
                db.add(config)
                await db.commit()

                result = await pypi_version_check.check_for_update(
                    db, "some-package", config, "1.0.0"
                )
                await db.commit()
                return result, config.latest_pypi_version

        result, persisted_latest_version = _run(_scenario())

        assert result.latest_version == "9.9.9"
        assert result.update_available is True
        assert persisted_latest_version == "9.9.9"

    def test_update_not_available_when_versions_match(self, engine, monkeypatch):
        async def fake_fetch(package_name, timeout_seconds=5.0):
            return "1.0.0"

        monkeypatch.setattr(pypi_version_check, "fetch_latest_pypi_version", fake_fetch)
        session_factory = _session_factory(engine)

        async def _scenario():
            async with session_factory() as db:
                config = FakeToolConfig()
                db.add(config)
                await db.commit()
                return await pypi_version_check.check_for_update(
                    db, "some-package", config, "1.0.0"
                )

        result = _run(_scenario())

        assert result.update_available is False

    def test_none_update_available_when_fetch_fails(self, engine, monkeypatch):
        async def fake_fetch(package_name, timeout_seconds=5.0):
            return None

        monkeypatch.setattr(pypi_version_check, "fetch_latest_pypi_version", fake_fetch)
        session_factory = _session_factory(engine)

        async def _scenario():
            async with session_factory() as db:
                config = FakeToolConfig()
                db.add(config)
                await db.commit()
                return await pypi_version_check.check_for_update(
                    db, "some-package", config, "1.0.0"
                )

        result = _run(_scenario())

        assert result.latest_version is None
        assert result.update_available is None
