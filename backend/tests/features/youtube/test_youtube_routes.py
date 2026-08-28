from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import get_read_db
from app.core.exceptions import AppHTTPException, register_exception_handlers
from app.features.youtube.routers import youtube_routes
from app.features.youtube.schemas.youtube_schemas import (
    YoutubeCommentsResponse,
    YoutubeLookupResponse,
    YoutubeOembedData,
)


@pytest.fixture
def client():
    async def _get_read_db() -> AsyncGenerator[None]:
        yield None

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    register_exception_handlers(app)
    app.include_router(youtube_routes.router)
    app.dependency_overrides[get_read_db] = _get_read_db
    return TestClient(app)


class TestLookupYoutubeVideo:
    def test_delegates_to_the_lookup_service_and_returns_its_response(self, client, monkeypatch):
        async def fake_perform_youtube_lookup(request, db):
            assert request.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            return YoutubeLookupResponse(
                video_id="dQw4w9WgXcQ",
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                oembed=YoutubeOembedData(title="Never Gonna Give You Up"),
                api_configured=False,
            )

        monkeypatch.setattr(youtube_routes, "perform_youtube_lookup", fake_perform_youtube_lookup)

        response = client.post(
            "/api/youtube/lookup",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["video_id"] == "dQw4w9WgXcQ"
        assert body["oembed"]["title"] == "Never Gonna Give You Up"

    def test_an_unrecognized_url_maps_to_the_services_400(self, client, monkeypatch):
        async def fake_perform_youtube_lookup(request, db):
            raise AppHTTPException(
                status_code=400,
                detail="Not a recognized YouTube video URL",
                error_code="YOUTUBE_INVALID_URL",
            )

        monkeypatch.setattr(youtube_routes, "perform_youtube_lookup", fake_perform_youtube_lookup)

        response = client.post("/api/youtube/lookup", json={"url": "https://example.com"})

        assert response.status_code == 400
        assert response.json()["error_code"] == "YOUTUBE_INVALID_URL"

    def test_rejects_an_empty_url_with_422(self, client):
        response = client.post("/api/youtube/lookup", json={"url": "  "})
        assert response.status_code == 422

    def test_rejects_a_missing_url_with_422(self, client):
        response = client.post("/api/youtube/lookup", json={})
        assert response.status_code == 422


class TestListYoutubeComments:
    def test_delegates_to_the_comments_service_and_returns_its_response(self, client, monkeypatch):
        async def fake_perform_youtube_comments_lookup(request, db):
            assert request.url == "https://youtu.be/dQw4w9WgXcQ"
            assert request.query == "spam"
            return YoutubeCommentsResponse(
                video_id="dQw4w9WgXcQ",
                comments=[],
                query="spam",
                truncated=True,
                pages_scanned=3,
            )

        monkeypatch.setattr(
            youtube_routes,
            "perform_youtube_comments_lookup",
            fake_perform_youtube_comments_lookup,
        )

        response = client.post(
            "/api/youtube/comments",
            json={"url": "https://youtu.be/dQw4w9WgXcQ", "query": "spam"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["video_id"] == "dQw4w9WgXcQ"
        assert body["truncated"] is True
        assert body["pages_scanned"] == 3

    def test_missing_api_key_maps_to_the_services_400(self, client, monkeypatch):
        async def fake_perform_youtube_comments_lookup(request, db):
            raise AppHTTPException(
                status_code=400,
                detail="A YouTube Data API key is required for comments.",
                error_code="YOUTUBE_COMMENTS_NOT_CONFIGURED",
            )

        monkeypatch.setattr(
            youtube_routes,
            "perform_youtube_comments_lookup",
            fake_perform_youtube_comments_lookup,
        )

        response = client.post(
            "/api/youtube/comments", json={"url": "https://youtu.be/dQw4w9WgXcQ"}
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "YOUTUBE_COMMENTS_NOT_CONFIGURED"

    def test_rejects_an_empty_url_with_422(self, client):
        response = client.post("/api/youtube/comments", json={"url": ""})
        assert response.status_code == 422

    def test_defaults_query_to_none_and_order_to_relevance(self, client, monkeypatch):
        captured = {}

        async def fake_perform_youtube_comments_lookup(request, db):
            captured["query"] = request.query
            captured["order"] = request.order
            return YoutubeCommentsResponse(video_id="dQw4w9WgXcQ")

        monkeypatch.setattr(
            youtube_routes,
            "perform_youtube_comments_lookup",
            fake_perform_youtube_comments_lookup,
        )

        response = client.post(
            "/api/youtube/comments", json={"url": "https://youtu.be/dQw4w9WgXcQ"}
        )

        assert response.status_code == 200
        assert captured == {"query": None, "order": "relevance"}
