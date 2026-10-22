"""Investigations API end to end on in-memory SQLite: CRUD, items across features, tombstones,
the combined report and the entity graph."""

import datetime
from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import AppHTTPException, http_exception_handler
from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult
from app.features.investigations.models.investigation_models import (
    Investigation,
    InvestigationItem,
)
from app.features.investigations.routers import investigation_routes
from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupResult,
    SingleLookupSearch,
)
from app.features.reddit_search.models.reddit_search_models import RedditSearch, RedditSearchResult
from app.features.username_search.models.username_search_models import (
    MaigretSearch,
    MaigretSiteResult,
)
from tests.conftest import run

T0 = datetime.datetime(2026, 10, 1, 12, 0, tzinfo=datetime.UTC)


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory(
        [
            model.__table__
            for model in (
                Investigation,
                InvestigationItem,
                SingleLookupSearch,
                SingleLookupResult,
                MaigretSearch,
                MaigretSiteResult,
                MailSearch,
                MailSearchResult,
                RedditSearch,
                RedditSearchResult,
            )
        ]
    )


@pytest.fixture
def client(session_factory):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    app = FastAPI()
    app.include_router(investigation_routes.router)
    app.add_exception_handler(AppHTTPException, http_exception_handler)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


@pytest.fixture
def runs(session_factory):
    """One related run per feature: an email lookup, a user_scanner run on the same address, a
    maigret run on its local part, and a Reddit search on that username."""

    async def _insert():
        async with session_factory() as db:
            lookup = SingleLookupSearch(
                ioc="jdoe@x.com",
                ioc_type="Email",
                searched_at=T0,
                results=[
                    SingleLookupResult(
                        service_key="haveibeenpwned",
                        service_name="Have I Been Pwned",
                        status="found",
                        summary="1 breach",
                        tlp="WHITE",
                        data=[{"Name": "LinkedIn"}],
                    )
                ],
            )
            mail = MailSearch(
                username="jdoe@x.com",
                source="user_scanner",
                status="completed",
                found_count=1,
                started_at=T0,
                provider_results=[MailSearchResult(provider_name="Spotify", emails=["jdoe@x.com"])],
            )
            maigret = MaigretSearch(
                username="jdoe",
                status="completed",
                found_count=1,
                started_at=T0,
                site_results=[
                    MaigretSiteResult(site_name="GitHub", url_user="https://github.com/JDoe")
                ],
            )
            reddit = RedditSearch(
                username="jdoe",
                searched_at=T0,
                results=[
                    RedditSearchResult(
                        kind="post",
                        reddit_id="a",
                        subreddit="osint",
                        title="hello",
                        permalink="/r/osint/a",
                        created_utc=1_700_000_000,
                    )
                ],
            )
            db.add_all([lookup, mail, maigret, reddit])
            await db.commit()
            return {
                "ioc_lookup": lookup.id,
                "email_search": mail.id,
                "username_search": maigret.id,
                "reddit_search": reddit.id,
            }

    return run(_insert())


def _create(client, name="Case A", notes=None):
    response = client.post("/api/investigations", json={"name": name, "notes": notes})
    assert response.status_code == 201, response.text
    return response.json()


def _add_all(client, investigation_id, runs):
    for feature, run_id in runs.items():
        response = client.post(
            f"/api/investigations/{investigation_id}/items",
            json={"feature": feature, "run_id": run_id, "note": f"{feature} note"},
        )
        assert response.status_code == 201, response.text


def test_create_list_rename_and_delete(client):
    created = _create(client, "  Case A  ", "first notes")
    assert created["name"] == "Case A"
    assert created["items"] == []

    listed = client.get("/api/investigations").json()
    assert [(i["name"], i["item_count"]) for i in listed] == [("Case A", 0)]

    patched = client.patch(f"/api/investigations/{created['id']}", json={"name": "Case B"})
    assert patched.status_code == 200
    assert (patched.json()["name"], patched.json()["notes"]) == ("Case B", "first notes")

    cleared = client.patch(f"/api/investigations/{created['id']}", json={"notes": None})
    assert cleared.json()["notes"] is None

    assert client.delete(f"/api/investigations/{created['id']}").status_code == 204
    assert client.get(f"/api/investigations/{created['id']}").status_code == 404


def test_blank_name_is_rejected(client):
    assert client.post("/api/investigations", json={"name": "   "}).status_code == 422


def test_add_items_across_features(client, runs):
    investigation = _create(client)
    _add_all(client, investigation["id"], runs)

    detail = client.get(f"/api/investigations/{investigation['id']}").json()

    assert {(i["feature"], i["target"], i["missing"]) for i in detail["items"]} == {
        ("ioc_lookup", "jdoe@x.com", False),
        ("email_search", "jdoe@x.com", False),
        ("username_search", "jdoe", False),
        ("reddit_search", "jdoe", False),
    }
    assert client.get("/api/investigations").json()[0]["item_count"] == 4
    memberships = client.get(
        "/api/investigations/memberships",
        params={"feature": "username_search", "run_id": runs["username_search"]},
    ).json()
    assert [m["id"] for m in memberships] == [investigation["id"]]


def test_add_item_errors(client, runs):
    investigation = _create(client)
    url = f"/api/investigations/{investigation['id']}/items"

    unsupported = client.post(url, json={"feature": "amass", "run_id": 1})
    assert unsupported.status_code == 422
    assert unsupported.json()["error_code"] == "INVESTIGATION_FEATURE_UNSUPPORTED"

    no_run = client.post(url, json={"feature": "ioc_lookup", "run_id": 999})
    assert no_run.json()["error_code"] == "INVESTIGATION_RUN_NOT_FOUND"

    body = {"feature": "ioc_lookup", "run_id": runs["ioc_lookup"]}
    assert client.post(url, json=body).status_code == 201
    duplicate = client.post(url, json=body)
    assert duplicate.status_code == 409

    missing_investigation = client.post("/api/investigations/999/items", json=body)
    assert missing_investigation.status_code == 404


def test_edit_and_remove_an_item(client, runs):
    investigation = _create(client)
    url = f"/api/investigations/{investigation['id']}/items"
    item = client.post(url, json={"feature": "reddit_search", "run_id": runs["reddit_search"]})
    item_id = item.json()["id"]

    edited = client.patch(f"{url}/{item_id}", json={"note": "same person"})
    assert edited.status_code == 200
    assert edited.json()["note"] == "same person"

    assert client.delete(f"{url}/{item_id}").status_code == 204
    assert client.delete(f"{url}/{item_id}").status_code == 404
    assert client.get(f"/api/investigations/{investigation['id']}").json()["items"] == []


def _delete_run(session_factory, model, run_id):
    async def _delete():
        async with session_factory() as db:
            await db.delete(await db.get(model, run_id))
            await db.commit()

    run(_delete())


def test_a_deleted_run_becomes_a_tombstone(client, runs, session_factory):
    investigation = _create(client)
    _add_all(client, investigation["id"], runs)
    _delete_run(session_factory, MaigretSearch, runs["username_search"])

    detail = client.get(f"/api/investigations/{investigation['id']}").json()
    item = next(i for i in detail["items"] if i["feature"] == "username_search")
    assert item["missing"] is True
    assert (item["target"], item["note"]) == ("jdoe", "username_search note")

    report = client.get(f"/api/investigations/{investigation['id']}/report").text
    assert "Run deleted from history" in report
    assert "Deleted from history" in report


def test_a_reused_run_id_is_a_tombstone_not_the_new_run(client, runs, session_factory):
    """SQLite reuses the highest rowid after a delete: a new run landing on the deleted run's id
    must not be shown as the item's run."""
    investigation = _create(client)
    _add_all(client, investigation["id"], runs)
    _delete_run(session_factory, MaigretSearch, runs["username_search"])

    async def _reinsert():
        async with session_factory() as db:
            db.add(
                MaigretSearch(
                    id=runs["username_search"],
                    username="someone-else",
                    status="completed",
                    found_count=1,
                    started_at=T0,
                    site_results=[
                        MaigretSiteResult(site_name="GitLab", url_user="https://gitlab.com/other")
                    ],
                )
            )
            await db.commit()

    run(_reinsert())

    detail = client.get(f"/api/investigations/{investigation['id']}").json()
    item = next(i for i in detail["items"] if i["feature"] == "username_search")
    assert item["missing"] is True
    report = client.get(f"/api/investigations/{investigation['id']}/report").text
    assert "someone-else" not in report
    assert "gitlab.com/other" not in report


def test_report_concatenates_each_features_sections(client, runs):
    investigation = _create(client, "Case <A>", "analyst notes")
    _add_all(client, investigation["id"], runs)

    response = client.get(f"/api/investigations/{investigation['id']}/report")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'filename="investigation-' in response.headers["content-disposition"]
    html = response.text
    assert "Case &lt;A&gt;" in html
    for title in (
        "Items per feature",
        "Service results",
        "Email search",
        "Found accounts",
        "Most active subreddits",
        "Top connected entities",
        "analyst notes",
        "reddit_search note",
    ):
        assert title in html, title


def test_report_as_pdf(client, runs):
    investigation = _create(client)
    _add_all(client, investigation["id"], runs)

    response = client.get(
        f"/api/investigations/{investigation['id']}/report", params={"format": "pdf"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def _component_of(graph, start):
    adjacent = {}
    for edge in graph["edges"]:
        adjacent.setdefault(edge["source"], set()).add(edge["target"])
        adjacent.setdefault(edge["target"], set()).add(edge["source"])
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(adjacent.get(node, ()))
    return seen


def test_graph_connects_related_runs_into_one_component(client, runs):
    investigation = _create(client)
    _add_all(client, investigation["id"], runs)

    graph = client.get(f"/api/investigations/{investigation['id']}/graph").json()

    ids = {node["id"] for node in graph["nodes"]}
    assert _component_of(graph, "email:jdoe@x.com") == ids
    assert {
        "email:jdoe@x.com",
        "username:jdoe",
        "breach:linkedin",
        "account:spotify/jdoe@x.com",
        "account:https://github.com/jdoe",
        "subreddit:osint",
    } == ids
    email = next(node for node in graph["nodes"] if node["id"] == "email:jdoe@x.com")
    assert email["is_root"]
    assert {(s["feature"]) for s in email["sources"]} == {"ioc_lookup", "email_search"}
    assert not graph["truncated"]
    assert "username" in graph["entity_types"]
    github = next(n for n in graph["nodes"] if n["id"] == "account:https://github.com/jdoe")
    assert github["raw_value"] == "https://github.com/JDoe"  # opened as found, case kept


def test_graph_type_filter_and_cap(client, runs, monkeypatch):
    from app.core.entities import graph as entity_graph

    investigation = _create(client)
    _add_all(client, investigation["id"], runs)
    url = f"/api/investigations/{investigation['id']}/graph"

    filtered = client.get(url, params=[("types", "username"), ("types", "subreddit")]).json()
    assert {node["type"] for node in filtered["nodes"]} == {"username", "subreddit"}
    assert filtered["total_nodes"] == 2

    monkeypatch.setattr(entity_graph, "MAX_GRAPH_NODES", 2)
    capped = client.get(url).json()
    assert capped["truncated"] is True
    assert capped["total_nodes"] == 6
    assert len(capped["nodes"]) == 2
    # Counted before the cap, so the filter still offers types the cap dropped entirely.
    assert capped["type_counts"] == {
        "email": 1,
        "username": 1,
        "breach": 1,
        "account": 2,
        "subreddit": 1,
    }
    assert filtered["type_counts"] == capped["type_counts"]


def test_supported_features(client):
    features = {f["feature"] for f in client.get("/api/investigations/features").json()}
    assert features == {"ioc_lookup", "username_search", "email_search", "reddit_search"}


def test_deleting_an_investigation_removes_its_items_not_the_runs(client, runs, session_factory):
    investigation = _create(client)
    _add_all(client, investigation["id"], runs)

    assert client.delete(f"/api/investigations/{investigation['id']}").status_code == 204

    async def _counts():
        async with session_factory() as db:
            from sqlalchemy import func, select

            items = await db.scalar(select(func.count(InvestigationItem.id)))
            lookups = await db.scalar(select(func.count(SingleLookupSearch.id)))
            return items, lookups

    assert run(_counts()) == (0, 1)


def test_a_concurrent_duplicate_add_is_a_409_not_a_500(client, runs, monkeypatch):
    """A double click: both requests pass find_item, the unique constraint decides."""
    from app.features.investigations.crud import investigation_crud

    investigation = _create(client)
    url = f"/api/investigations/{investigation['id']}/items"
    body = {"feature": "ioc_lookup", "run_id": runs["ioc_lookup"]}
    assert client.post(url, json=body).status_code == 201

    async def _never_found(*_args):
        return None

    monkeypatch.setattr(investigation_crud, "find_item", _never_found)
    response = client.post(url, json=body)

    assert response.status_code == 409
    assert response.json()["error_code"] == "INVESTIGATION_ITEM_EXISTS"


def test_memberships_report_each_investigations_real_item_count(client, runs):
    first = _create(client, "A")
    _add_all(client, first["id"], runs)
    _create(client, "B")

    memberships = client.get(
        "/api/investigations/memberships",
        params={"feature": "reddit_search", "run_id": runs["reddit_search"]},
    ).json()

    assert [(m["name"], m["item_count"]) for m in memberships] == [("A", 4)]


def test_detail_and_note_edits_never_load_runs_results(client, runs, monkeypatch):
    """Only report/graph need results; the detail view and notes saves check existence only."""
    import dataclasses

    from app.utils import run_source_registry

    investigation = _create(client)
    _add_all(client, investigation["id"], runs)

    async def _boom(*_args):
        raise AssertionError("loaded a run's results")

    for key, source in list(run_source_registry.RUN_SOURCES.items()):
        monkeypatch.setitem(
            run_source_registry.RUN_SOURCES, key, dataclasses.replace(source, load=_boom)
        )
    url = f"/api/investigations/{investigation['id']}"

    detail = client.get(url)
    assert detail.status_code == 200
    assert not any(item["missing"] for item in detail.json()["items"])
    assert client.patch(url, json={"notes": "x"}).status_code == 200
    item_id = detail.json()["items"][0]["id"]
    assert client.patch(f"{url}/items/{item_id}", json={"note": "y"}).status_code == 200
    assert (
        client.post(url + "/items", json={"feature": "ioc_lookup", "run_id": 999}).json()[
            "error_code"
        ]
        == "INVESTIGATION_RUN_NOT_FOUND"
    )
