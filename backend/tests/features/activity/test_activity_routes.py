"""Cross-feature activity feed: merges every scan feature's runs with the non-scan histories."""

import datetime
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_read_db
from app.features.activity.routers import activity_routes
from app.features.amass.models.amass_models import AmassSearch
from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupSearch,
)
from app.features.reddit_search.models.reddit_search_models import RedditSearch
from app.features.username_search.models.username_search_models import MaigretSearch
from app.utils.scan_reconciliation_registry import all_scan_features
from tests.conftest import run

T0 = datetime.datetime(2026, 10, 1, 12, 0, tzinfo=datetime.UTC)


@pytest.fixture
def session_factory(make_session_factory):
    tables = [feature.model.__table__ for feature in all_scan_features()]
    tables += [SingleLookupSearch.__table__, RedditSearch.__table__]
    return make_session_factory(tables)


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db

    app = FastAPI()
    app.include_router(activity_routes.router)
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _seed(session_factory, *rows):
    async def _insert():
        async with session_factory() as db:
            db.add_all(rows)
            await db.commit()

    run(_insert())


def test_merges_features_newest_first(client, session_factory):
    _seed(
        session_factory,
        AmassSearch(domain="example.com", status="completed", searched_at=T0),
        MaigretSearch(
            username="alice",
            source="maigret",
            status="failed",
            started_at=T0 + datetime.timedelta(minutes=2),
        ),
        SingleLookupSearch(
            ioc="1.2.3.4", ioc_type="IPv4", searched_at=T0 + datetime.timedelta(minutes=1)
        ),
        RedditSearch(username="bob", searched_at=T0 - datetime.timedelta(minutes=1)),
    )

    response = client.get("/api/activity")

    assert response.status_code == 200
    items = response.json()
    assert [(i["feature"], i["target"], i["status"]) for i in items] == [
        ("username_search", "alice", "failed"),
        ("ioc_lookup", "1.2.3.4", "completed"),
        ("amass", "example.com", "completed"),
        ("reddit_search", "bob", "completed"),
    ]


def test_respects_limit(client, session_factory):
    _seed(
        session_factory,
        *[
            AmassSearch(
                domain=f"d{i}.com",
                status="completed",
                searched_at=T0 + datetime.timedelta(minutes=i),
            )
            for i in range(5)
        ],
    )

    items = client.get("/api/activity", params={"limit": 2}).json()

    assert [i["target"] for i in items] == ["d4.com", "d3.com"]


def test_empty_when_nothing_has_run(client):
    assert client.get("/api/activity").json() == []


def test_every_scan_feature_target_column_exists():
    for feature in all_scan_features():
        assert hasattr(feature.model, feature.target_column), feature.name


def test_active_lists_only_unfinished_runs_and_marks_queued_ones(
    client, session_factory, monkeypatch
):
    from app.core.scans.run import ScanRun

    _seed(
        session_factory,
        AmassSearch(domain="done.com", status="completed", searched_at=T0),
        AmassSearch(domain="busy.com", status="running", searched_at=T0),
        AmassSearch(
            domain="waiting.com",
            status="running",
            searched_at=T0 + datetime.timedelta(minutes=1),
        ),
        MaigretSearch(
            username="alice",
            source="maigret",
            status="running",
            # Far older than anything the recent feed would still show - must stay listed.
            started_at=T0 - datetime.timedelta(days=30),
        ),
    )
    # Only the in-memory queue knows a run is waiting rather than running.
    monkeypatch.setattr(ScanRun, "_queued", {(AmassSearch, 3): object()})

    response = client.get("/api/activity/active")

    assert response.status_code == 200
    assert [(i["feature"], i["target"], i["status"]) for i in response.json()] == [
        ("amass", "waiting.com", "queued"),
        ("amass", "busy.com", "running"),
        ("username_search", "alice", "running"),
    ]


def test_active_is_empty_with_nothing_running(client, session_factory):
    _seed(session_factory, AmassSearch(domain="done.com", status="completed", searched_at=T0))

    assert client.get("/api/activity/active").json() == []
