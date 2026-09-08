"""Coverage for store_article_async's keyword-watchlist alert: a newsfeed
article matching a configured keyword (core/settings/keywords/) raises an
alert (in-app + optional Telegram, see alerts_service.raise_alert) - a
duplicate (already-stored) article or one with no match must not."""

import contextlib

import pytest
from sqlalchemy import select

import app.features.newsfeed.service.feed_processing_service as feed_processing_service
from app.core.alerts.models.alerts_models import Alert
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.features.newsfeed.models.newsfeed_models import NewsArticle
from app.features.newsfeed.service.feed_processing_service import store_article_async
from tests.conftest import run as _run

ENTRY = {"name": "Example Feed", "icon": "icon.png"}
POST = {
    "title": "Ransomware hits a hospital",
    "summary": "Details about the incident.",
    "link": "https://example.com/article-1",
}


@pytest.fixture
def factory(monkeypatch, make_session_factory):
    factory = make_session_factory(
        [NewsArticle.__table__, Alert.__table__, TelegramSettings.__table__]
    )

    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with factory() as db:
            yield db
            await db.commit()

    monkeypatch.setattr(feed_processing_service, "managed_session", fake_managed_session)
    return factory


async def _alert_titles(factory):
    async with factory() as db:
        result = await db.execute(select(Alert.title))
        return list(result.scalars().all())


class TestKeywordMatchAlert:
    def test_match_raises_an_alert(self, factory):
        _run(
            store_article_async(
                ENTRY, POST, "", None, keyword_matching_enabled=True, keywords=["ransomware"]
            )
        )

        assert _run(_alert_titles(factory)) == ["Newsfeed keyword match"]

    def test_alert_names_the_matched_keyword_and_link_not_the_key_material(self, factory):
        _run(
            store_article_async(
                ENTRY, POST, "", None, keyword_matching_enabled=True, keywords=["ransomware"]
            )
        )

        async def _message():
            async with factory() as db:
                result = await db.execute(select(Alert.message))
                return result.scalar_one()

        message = _run(_message())
        assert "ransomware" in message
        assert POST["link"] in message
        assert ENTRY["name"] in message

    def test_no_match_does_not_raise_an_alert(self, factory):
        _run(
            store_article_async(
                ENTRY, POST, "", None, keyword_matching_enabled=True, keywords=["phishing"]
            )
        )

        assert _run(_alert_titles(factory)) == []

    def test_keyword_matching_disabled_does_not_raise_an_alert(self, factory):
        _run(
            store_article_async(
                ENTRY, POST, "", None, keyword_matching_enabled=False, keywords=["ransomware"]
            )
        )

        assert _run(_alert_titles(factory)) == []

    def test_duplicate_article_does_not_raise_a_second_alert(self, factory):
        _run(
            store_article_async(
                ENTRY, POST, "", None, keyword_matching_enabled=True, keywords=["ransomware"]
            )
        )
        _run(
            store_article_async(
                ENTRY, POST, "", None, keyword_matching_enabled=True, keywords=["ransomware"]
            )
        )

        assert _run(_alert_titles(factory)) == ["Newsfeed keyword match"]
