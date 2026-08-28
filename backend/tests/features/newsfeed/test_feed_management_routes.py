"""HTTP-level coverage for feed_management_routes.py. Favicon downloading and
image processing (icon_management_service.py / utils/validation.py) are
network/filesystem-heavy and each deserve their own dedicated tests, so this
mocks them at the router boundary and only checks the route wires requests
into them, maps their results to the right status codes, and (for
get_feed_icon) actually serves a file from the real static directory."""

import base64
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.exceptions import register_exception_handlers
from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings
from app.features.newsfeed.routers import feed_management_routes
from app.features.newsfeed.schemas.newsfeed_schemas import FeedInfo, NewsfeedSettingsSchema


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
    app.include_router(feed_management_routes.router)
    app.dependency_overrides[get_db] = _get_db
    return TestClient(app)


def _b64(name: str) -> str:
    return base64.b64encode(name.encode("utf-8")).decode("ascii")


async def _fake_save_icon(data, icon_id):
    return True, None


class TestValidateFeedUrl:
    def test_returns_the_parsed_feed_info_when_valid(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes,
            "validate_feed",
            lambda url: (True, None, FeedInfo(title="Feed A", entry_count=5)),
        )

        response = client.post(
            "/api/settings/modules/newsfeed/validation",
            json={"name": "feed-a", "url": "https://feed-a.example/rss"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is True
        assert body["feed_info"]["title"] == "Feed A"

    def test_returns_400_when_invalid(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes, "validate_feed", lambda url: (False, "Not an RSS feed", None)
        )

        response = client.post(
            "/api/settings/modules/newsfeed/validation",
            json={"name": "feed-a", "url": "https://feed-a.example/rss"},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_INVALID_URL"


class TestAddCustomFeed:
    def test_creates_a_feed_after_validation(self, client, monkeypatch):
        monkeypatch.setattr(feed_management_routes, "validate_feed", lambda url: (True, None, None))

        async def fake_create(db, settings):
            return NewsfeedSettingsSchema.model_validate(
                {"name": settings.name, "url": str(settings.url)}
            )

        monkeypatch.setattr(feed_management_routes, "create_custom_feed_with_favicon", fake_create)

        response = client.post(
            "/api/settings/modules/newsfeed",
            json={"name": "feed-a", "url": "https://feed-a.example/rss"},
        )

        assert response.status_code == 201
        assert response.json()["name"] == "feed-a"

    def test_rejects_an_invalid_feed_url(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes, "validate_feed", lambda url: (False, "unreachable", None)
        )

        response = client.post(
            "/api/settings/modules/newsfeed",
            json={"name": "feed-a", "url": "https://feed-a.example/rss"},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_INVALID_URL"

    def test_rejects_a_duplicate_feed_name(self, client, session_factory, monkeypatch):
        monkeypatch.setattr(feed_management_routes, "validate_feed", lambda url: (True, None, None))

        async def _seed():
            async with session_factory() as db:
                db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
                await db.commit()

        import asyncio

        asyncio.run(_seed())

        response = client.post(
            "/api/settings/modules/newsfeed",
            json={"name": "feed-a", "url": "https://feed-a.example/other-rss"},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_NAME_EXISTS"


class TestUploadFeedIcon:
    def test_uploads_and_processes_the_icon(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes,
            "validate_and_process_icon",
            lambda content, filename: (True, None, (b"resized-bytes", "abc123.png")),
        )
        monkeypatch.setattr(feed_management_routes, "save_icon", _fake_save_icon)

        async def fake_update_feed_icon(db, name, icon_id):
            assert name == "feed-a"
            assert icon_id == "abc123.png"
            return NewsfeedSettings(name=name, url="https://feed-a.example/rss")

        monkeypatch.setattr(feed_management_routes, "update_feed_icon", fake_update_feed_icon)

        async def fake_sync(db, name, icon):
            return None

        monkeypatch.setattr(feed_management_routes, "sync_article_icons", fake_sync)

        response = client.put(
            f"/api/settings/modules/newsfeed/{_b64('feed-a')}/icon",
            files={"file": ("icon.png", b"raw-bytes", "image/png")},
        )

        assert response.status_code == 200
        assert response.json()["icon_id"] == "abc123.png"

    def test_rejects_an_invalid_base64_feed_name(self, client):
        response = client.put(
            "/api/settings/modules/newsfeed/not-valid-base64!!!/icon",
            files={"file": ("icon.png", b"raw-bytes", "image/png")},
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_INVALID_NAME_ENCODING"

    def test_rejects_an_invalid_icon_file(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes,
            "validate_and_process_icon",
            lambda content, filename: (False, "Not an image", None),
        )

        response = client.put(
            f"/api/settings/modules/newsfeed/{_b64('feed-a')}/icon",
            files={"file": ("icon.txt", b"not-an-image", "text/plain")},
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_ICON_INVALID"

    def test_returns_404_when_the_feed_does_not_exist(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes,
            "validate_and_process_icon",
            lambda content, filename: (True, None, (b"resized-bytes", "abc123.png")),
        )
        monkeypatch.setattr(feed_management_routes, "save_icon", _fake_save_icon)

        async def fake_update_feed_icon(db, name, icon_id):
            return None

        monkeypatch.setattr(feed_management_routes, "update_feed_icon", fake_update_feed_icon)

        response = client.put(
            f"/api/settings/modules/newsfeed/{_b64('absent')}/icon",
            files={"file": ("icon.png", b"raw-bytes", "image/png")},
        )

        assert response.status_code == 404
        assert response.json()["error_code"] == "FEED_NOT_FOUND"

    def test_returns_500_when_saving_the_icon_fails(self, client, monkeypatch):
        monkeypatch.setattr(
            feed_management_routes,
            "validate_and_process_icon",
            lambda content, filename: (True, None, (b"resized-bytes", "abc123.png")),
        )

        async def fake_save_icon_failure(data, icon_id):
            return False, "Disk full"

        monkeypatch.setattr(feed_management_routes, "save_icon", fake_save_icon_failure)

        response = client.put(
            f"/api/settings/modules/newsfeed/{_b64('feed-a')}/icon",
            files={"file": ("icon.png", b"raw-bytes", "image/png")},
        )

        assert response.status_code == 500
        assert response.json()["error_code"] == "FEED_ICON_SAVE_FAILED"


class TestDeleteFeedIcon:
    def test_returns_404_when_the_feed_does_not_exist(self, client, monkeypatch):
        async def fake_delete(db, name):
            return False, "Feed not found"

        monkeypatch.setattr(
            feed_management_routes, "delete_feed_icon_with_favicon_fallback", fake_delete
        )

        response = client.delete(f"/api/settings/modules/newsfeed/{_b64('absent')}/icon")

        assert response.status_code == 404
        assert response.json()["error_code"] == "FEED_NOT_FOUND"

    def test_deletes_the_icon(self, client, monkeypatch):
        async def fake_delete(db, name):
            return True, "Icon deleted, using favicon"

        monkeypatch.setattr(
            feed_management_routes, "delete_feed_icon_with_favicon_fallback", fake_delete
        )

        response = client.delete(f"/api/settings/modules/newsfeed/{_b64('feed-a')}/icon")

        assert response.status_code == 200
        assert response.json()["message"] == "Icon deleted, using favicon"


class TestRefetchFeedFavicon:
    def test_returns_404_when_the_feed_does_not_exist(self, client, monkeypatch):
        async def fake_refetch(db, name):
            return False, "Feed not found", None

        monkeypatch.setattr(feed_management_routes, "refetch_feed_favicon", fake_refetch)

        response = client.post(f"/api/settings/modules/newsfeed/{_b64('absent')}/icon/refetch")

        assert response.status_code == 404
        assert response.json()["error_code"] == "FEED_NOT_FOUND"

    def test_returns_the_refetch_result_on_success(self, client, monkeypatch):
        async def fake_refetch(db, name):
            return True, "Favicon downloaded", "new-icon.png"

        monkeypatch.setattr(feed_management_routes, "refetch_feed_favicon", fake_refetch)

        response = client.post(f"/api/settings/modules/newsfeed/{_b64('feed-a')}/icon/refetch")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["icon_id"] == "new-icon.png"

    def test_returns_200_with_success_false_on_a_non_404_failure(self, client, monkeypatch):
        async def fake_refetch(db, name):
            return False, "No favicon found on the site", None

        monkeypatch.setattr(feed_management_routes, "refetch_feed_favicon", fake_refetch)

        response = client.post(f"/api/settings/modules/newsfeed/{_b64('feed-a')}/icon/refetch")

        assert response.status_code == 200
        assert response.json()["success"] is False


class TestRefetchAllMissingFavicons:
    def test_summarizes_per_feed_results(self, client, monkeypatch):
        async def fake_get_feeds(db):
            return [
                NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"),
                NewsfeedSettings(name="feed-b", url="https://feed-b.example/rss"),
            ]

        monkeypatch.setattr(feed_management_routes, "get_feeds_with_default_icon", fake_get_feeds)

        async def fake_refetch(db, name):
            if name == "feed-a":
                return True, "ok", "icon-a.png"
            return False, "no favicon", None

        monkeypatch.setattr(feed_management_routes, "refetch_feed_favicon", fake_refetch)

        response = client.post("/api/settings/modules/newsfeed/icons/refetch-missing")

        assert response.status_code == 200
        body = response.json()
        assert body == {
            "total": 2,
            "succeeded": 1,
            "failed": 1,
            "results": [
                {"feed_name": "feed-a", "success": True, "icon_id": "icon-a.png", "error": None},
                {
                    "feed_name": "feed-b",
                    "success": False,
                    "icon_id": None,
                    "error": "no favicon",
                },
            ],
        }

    def test_no_feeds_with_default_icon_returns_zero_totals(self, client, monkeypatch):
        async def fake_get_feeds(db):
            return []

        monkeypatch.setattr(feed_management_routes, "get_feeds_with_default_icon", fake_get_feeds)

        response = client.post("/api/settings/modules/newsfeed/icons/refetch-missing")

        assert response.json() == {"total": 0, "succeeded": 0, "failed": 0, "results": []}


class TestDeleteCustomFeedRoute:
    def test_removes_a_custom_icon_file_before_deleting_the_feed(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                db.add(
                    NewsfeedSettings(
                        name="feed-a",
                        url="https://feed-a.example/rss",
                        icon="custom123.png",
                        icon_id="custom123.png",
                    )
                )
                await db.commit()

        import asyncio

        asyncio.run(_seed())

        # icon_id doesn't correspond to a real file on disk - remove_existing_icon is a
        # safe no-op for a missing path, so this just needs the branch to run.
        response = client.request(
            "DELETE", "/api/settings/modules/newsfeed", params={"feed_name": "feed-a"}
        )

        assert response.status_code == 200

    def test_returns_404_when_the_feed_does_not_exist(self, client):
        response = client.request(
            "DELETE", "/api/settings/modules/newsfeed", params={"feed_name": "absent"}
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "FEED_NOT_FOUND"

    def test_deletes_an_existing_feed(self, client, session_factory):
        async def _seed():
            async with session_factory() as db:
                db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
                await db.commit()

        import asyncio

        asyncio.run(_seed())

        response = client.request(
            "DELETE", "/api/settings/modules/newsfeed", params={"feed_name": "feed-a"}
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Feed deleted successfully"

    def test_returns_500_when_the_delete_itself_fails(self, client, session_factory, monkeypatch):
        async def _seed():
            async with session_factory() as db:
                db.add(NewsfeedSettings(name="feed-a", url="https://feed-a.example/rss"))
                await db.commit()

        import asyncio

        asyncio.run(_seed())

        async def fake_delete(db, name):
            return False

        monkeypatch.setattr(feed_management_routes, "delete_custom_feed", fake_delete)

        response = client.request(
            "DELETE", "/api/settings/modules/newsfeed", params={"feed_name": "feed-a"}
        )

        assert response.status_code == 500
        assert response.json()["error_code"] == "FEED_DELETE_FAILED"


class TestGetFeedIcon:
    def test_falls_back_to_the_default_icon_when_missing(self, client):
        response = client.get("/api/feedicons/does-not-exist.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_rejects_a_name_with_disallowed_characters(self, client):
        response = client.get("/api/feedicons/abc$%25xyz.png")

        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_ICON_INVALID_NAME"

    def test_rejects_a_name_containing_dot_dot(self, client):
        response = client.get("/api/feedicons/..etc.png")

        assert response.status_code == 400
        assert response.json()["error_code"] == "FEED_ICON_INVALID_NAME"
