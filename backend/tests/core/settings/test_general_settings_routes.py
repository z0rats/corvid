"""HTTP-level coverage for general_settings_routes.py: the base GET/PUT pair now
built on build_singleton_settings_router (GET on ReadSessionDep, safe since
GeneralSettings is guaranteed created by _run_application_defaults() at startup),
plus a regression check that the three hand-written PUTs (/darkmode, /language,
/command-palette) still work unchanged on the same router object."""
import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.settings.general.models.general_settings_models import GeneralSettings
from app.core.settings.general.routers.general_settings_routes import router


@pytest.fixture
def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[GeneralSettings.__table__])

    asyncio.run(_create_tables())

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestGetGeneralSettings:
    def test_creates_and_returns_defaults(self, client):
        response = client.get("/api/settings/general")

        assert response.status_code == 200
        body = response.json()
        assert body["darkmode"] is False
        assert body["language"] == "en"


class TestUpdateGeneralSettings:
    def test_updates_provided_fields(self, client):
        response = client.put("/api/settings/general", json={"darkmode": True, "language": "ru"})

        assert response.status_code == 200
        body = response.json()
        assert body["darkmode"] is True
        assert body["language"] == "ru"

    def test_invalid_language_returns_400(self, client):
        response = client.put("/api/settings/general", json={"language": "xx"})

        assert response.status_code == 400


class TestExtraPutsStillWork:
    """Regression: these three routes are added manually onto the same router
    object the factory returns, after the base GET/PUT pair migrated to it."""

    def test_darkmode_endpoint(self, client):
        response = client.put("/api/settings/general/darkmode", json={"darkmode": True})

        assert response.status_code == 200
        assert response.json()["darkmode"] is True

    def test_language_endpoint(self, client):
        response = client.put("/api/settings/general/language", json={"language": "ru"})

        assert response.status_code == 200
        assert response.json()["language"] == "ru"

    def test_command_palette_endpoint(self, client):
        response = client.put(
            "/api/settings/general/command-palette",
            json={"auto_open_on_single_match": False, "start_screen": "newsfeed", "always_tiles": True},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["auto_open_on_single_match"] is False
        assert body["start_screen"] == "newsfeed"
        assert body["always_tiles"] is True
