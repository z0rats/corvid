"""HTTP-level coverage for analysis_routes.py. The actual LLM call
(article_analysis_service.analyze_article_with_llm) has its own dedicated
tests in test_article_analysis_service.py, so this mocks it at the router
boundary and only checks the route resolves the article, resolves the
model_id, and wires the request into the service correctly."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import register_exception_handlers
from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings
from app.features.newsfeed.routers import analysis_routes
from app.features.newsfeed.schemas.newsfeed_schemas import AnalysisResultResponse


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([NewsfeedSettings.__table__, NewsArticle.__table__])


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(analysis_routes.router)
    app.dependency_overrides[get_db] = _get_db
    return TestClient(app)


def _seed_article(session_factory) -> int:
    async def _seed():
        async with session_factory() as db:
            db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
            await db.flush()
            article = NewsArticle(
                feedname="feed-a",
                icon="default.png",
                title="Ransomware gang hits a bank",
                summary="summary",
                date=datetime.now(UTC),
                link="https://feed-a.example/article-1",
            )
            db.add(article)
            await db.commit()
            return article.id

    return asyncio.run(_seed())


class TestAnalyzeNewsArticle:
    def test_returns_404_for_an_unknown_article(self, client):
        response = client.post("/api/newsfeed/analyze/999")

        assert response.status_code == 404
        assert response.json()["error_code"] == "ARTICLE_NOT_FOUND"

    def test_uses_the_explicit_model_id_without_resolving_a_default(
        self, client, session_factory, monkeypatch
    ):
        article_id = _seed_article(session_factory)
        captured = {}

        async def fake_get_default_model_id(db, module_key):
            raise AssertionError("should not resolve a default when model_id is given")

        async def fake_analyze(db, article_id, model_id, **kwargs):
            captured["model_id"] = model_id
            captured.update(kwargs)
            return AnalysisResultResponse(message="Analysis complete")

        monkeypatch.setattr(analysis_routes, "get_default_model_id", fake_get_default_model_id)
        monkeypatch.setattr(analysis_routes, "analyze_article_with_llm", fake_analyze)

        response = client.post(f"/api/newsfeed/analyze/{article_id}", json={"model_id": "gpt-4o"})

        assert response.status_code == 200
        assert captured["model_id"] == "gpt-4o"

    def test_resolves_the_default_model_id_when_omitted(self, client, session_factory, monkeypatch):
        article_id = _seed_article(session_factory)
        captured = {}

        async def fake_get_default_model_id(db, module_key):
            assert module_key == "newsfeed_analysis"
            return "resolved-default-model"

        async def fake_analyze(db, article_id, model_id, **kwargs):
            captured["model_id"] = model_id
            return AnalysisResultResponse(message="Analysis complete")

        monkeypatch.setattr(analysis_routes, "get_default_model_id", fake_get_default_model_id)
        monkeypatch.setattr(analysis_routes, "analyze_article_with_llm", fake_analyze)

        response = client.post(f"/api/newsfeed/analyze/{article_id}")

        assert response.status_code == 200
        assert captured["model_id"] == "resolved-default-model"

    def test_passes_through_the_request_params(self, client, session_factory, monkeypatch):
        article_id = _seed_article(session_factory)
        captured = {}

        async def fake_analyze(db, article_id, model_id, **kwargs):
            captured.update(kwargs)
            return AnalysisResultResponse(message="Analysis complete")

        monkeypatch.setattr(analysis_routes, "analyze_article_with_llm", fake_analyze)

        response = client.post(
            f"/api/newsfeed/analyze/{article_id}",
            json={
                "model_id": "gpt-4o",
                "temperature": 0.7,
                "max_tokens": 500,
                "use_cti_settings": False,
                "force": True,
                "mode": "mitre",
            },
        )

        assert response.status_code == 200
        assert captured == {
            "temperature": 0.7,
            "max_tokens": 500,
            "use_cti_settings": False,
            "force": True,
            "mode": "mitre",
        }

    def test_returns_the_analysis_result(self, client, session_factory, monkeypatch):
        article_id = _seed_article(session_factory)

        async def fake_analyze(db, article_id, model_id, **kwargs):
            return AnalysisResultResponse(
                message="Analysis complete",
                analysis_result={"verdict": "phishing"},
                cti_settings_used=True,
            )

        monkeypatch.setattr(analysis_routes, "analyze_article_with_llm", fake_analyze)

        response = client.post(f"/api/newsfeed/analyze/{article_id}", json={"model_id": "gpt-4o"})

        assert response.status_code == 200
        body = response.json()
        assert body["analysis_result"] == {"verdict": "phishing"}
        assert body["cti_settings_used"] is True

    def test_rejects_a_non_positive_article_id(self, client):
        response = client.post("/api/newsfeed/analyze/0")
        assert response.status_code == 422

    def test_rejects_an_out_of_range_temperature(self, client, session_factory):
        article_id = _seed_article(session_factory)

        response = client.post(f"/api/newsfeed/analyze/{article_id}", json={"temperature": 1.5})

        assert response.status_code == 422
