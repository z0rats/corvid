from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.features.image_tools.crud.geolocation_history_crud import create_search
from app.features.image_tools.models.geolocation_history_models import ImageGeolocationSearch
from app.features.image_tools.routers import geolocation_history_routes
from app.features.image_tools.schemas.image_schemas import (
    GeoCandidate,
    GeoClue,
    ImageGeolocationResponse,
)
from tests.conftest import run


def _sample_result() -> ImageGeolocationResponse:
    return ImageGeolocationResponse(
        candidates=[GeoCandidate(location="Serbia", confidence=0.6, reasoning="road signs")],
        clues=[GeoClue(category="signage_language", observation="Cyrillic", supports="Serbia")],
        caveats="Hypothesis only.",
        model_used="claude-sonnet-4-6",
    )


@pytest.fixture
def client(make_session_factory):
    session_factory = make_session_factory([ImageGeolocationSearch.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(geolocation_history_routes.router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app), session_factory


def _seed(session_factory, filename="street.jpg") -> int:
    async def _run():
        async with session_factory() as db:
            search = await create_search(db, filename, "a" * 64, _sample_result())
            await db.commit()
            return search.id

    return run(_run())


class TestListSearches:
    def test_returns_seeded_searches_most_recent_first(self, client):
        test_client, session_factory = client
        _seed(session_factory, "first.jpg")
        second_id = _seed(session_factory, "second.jpg")

        response = test_client.get("/api/image/geolocate/history")

        assert response.status_code == 200
        body = response.json()
        assert body[0]["id"] == second_id
        assert body[0]["top_candidate"] == "Serbia"

    def test_empty_history_returns_empty_list(self, client):
        test_client, _session_factory = client

        response = test_client.get("/api/image/geolocate/history")

        assert response.status_code == 200
        assert response.json() == []


class TestGetSearch:
    def test_returns_full_detail_including_clues(self, client):
        test_client, session_factory = client
        search_id = _seed(session_factory)

        response = test_client.get(f"/api/image/geolocate/history/{search_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["result"]["candidates"][0]["location"] == "Serbia"
        assert body["result"]["clues"][0]["category"] == "signage_language"

    def test_returns_404_for_unknown_id(self, client):
        test_client, _session_factory = client

        response = test_client.get("/api/image/geolocate/history/999")

        assert response.status_code == 404
        assert response.json()["error_code"] == "GEOLOCATION_HISTORY_NOT_FOUND"


class TestExportReport:
    def test_html_report_download(self, client):
        test_client, session_factory = client
        search_id = _seed(session_factory)

        response = test_client.get(f"/api/image/geolocate/history/{search_id}/report")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Serbia" in response.text

    def test_pdf_report_download(self, client):
        test_client, session_factory = client
        search_id = _seed(session_factory)

        response = test_client.get(
            f"/api/image/geolocate/history/{search_id}/report", params={"format": "pdf"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_returns_404_for_unknown_id(self, client):
        test_client, _session_factory = client

        response = test_client.get("/api/image/geolocate/history/999/report")

        assert response.status_code == 404


class TestDeleteSearch:
    def test_deletes_and_then_404s(self, client):
        test_client, session_factory = client
        search_id = _seed(session_factory)

        delete_response = test_client.delete(f"/api/image/geolocate/history/{search_id}")
        assert delete_response.status_code == 204

        get_response = test_client.get(f"/api/image/geolocate/history/{search_id}")
        assert get_response.status_code == 404

    def test_returns_404_for_unknown_id(self, client):
        test_client, _session_factory = client

        response = test_client.delete("/api/image/geolocate/history/999")

        assert response.status_code == 404
        assert response.json()["error_code"] == "GEOLOCATION_HISTORY_NOT_FOUND"
