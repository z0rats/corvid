"""`POST /api/username-search/scan/site-check` and the name-restricted site dict behind it."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.rate_limit_config import limiter
from app.core.exceptions import AppHTTPException
from app.features.username_search.config.maigret_config import (
    get_maigret_database,
    get_site_dict,
)
from app.features.username_search.routers import username_search_routes as routes


class TestGetSiteDictNames:
    def test_returns_exactly_the_named_sites_case_insensitively(self):
        assert list(get_site_dict(500, names=["github"])) == ["GitHub"]

    def test_a_low_ranked_site_is_not_cut_off_by_the_top_count(self):
        db = get_maigret_database()
        lowest = max(
            (s for s in db.sites if not s.disabled and s.type == "username"),
            key=lambda s: s.alexa_rank,
        )
        assert lowest.name in get_site_dict(1, names=[lowest.name])


class TestResolveSiteNames:
    def test_canonicalises_and_dedupes(self):
        assert routes._resolve_site_names(["github", "GITHUB", "Reddit"]) == ["GitHub", "Reddit"]

    def test_unknown_site_is_a_422(self):
        with pytest.raises(AppHTTPException) as exc:
            routes._resolve_site_names(["GitHub", "NoSuchSiteAnywhere"])
        assert exc.value.status_code == 422
        assert "NoSuchSiteAnywhere" in exc.value.detail


@pytest.fixture
def client(monkeypatch):
    limiter.reset()
    calls: list[dict] = []

    async def fake_run_scan(username, queue, **kwargs):
        calls.append({"username": username, **kwargs})
        queue.put_nowait(None)

    monkeypatch.setattr(routes, "run_maigret_scan", fake_run_scan)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(routes.router)
    test_client = TestClient(app)
    test_client.calls = calls  # type: ignore[attr-defined]
    yield test_client
    limiter.reset()


URL = "/api/username-search/scan/site-check"


class TestSiteCheckRoute:
    def test_runs_maigret_on_the_canonical_names_with_provenance(self, client):
        response = client.post(
            URL,
            json={
                "username": " jsmith ",
                "site_names": ["github"],
                "parent_search_id": 7,
                "pivot_source": " link from Reddit ",
            },
        )
        assert response.status_code == 200
        assert client.calls == [
            {
                "username": "jsmith",
                "site_names": ["GitHub"],
                "parent_search_id": 7,
                "pivot_source": "link from Reddit",
            }
        ]

    @pytest.mark.parametrize(
        "body",
        [
            {"username": "a", "site_names": []},
            {"username": "a", "site_names": ["GitHub"] * 6},
            {"username": "a", "site_names": ["GitHub"], "pivot_source": "x" * 201},
            {"username": "a", "site_names": ["GitHub"], "parent_search_id": 0},
            {"username": " ", "site_names": ["GitHub"]},
        ],
    )
    def test_invalid_bodies_are_422(self, client, body):
        assert client.post(URL, json=body).status_code == 422
        assert client.calls == []

    def test_unknown_site_is_422_and_starts_nothing(self, client):
        response = client.post(URL, json={"username": "a", "site_names": ["NoSuchSite"]})
        assert response.status_code == 422
        assert client.calls == []

    def test_limit_is_five_per_minute_not_the_scan_routes_three(self, client):
        body = {"username": "a", "site_names": ["GitHub"]}
        codes = [client.post(URL, json=body).status_code for _ in range(6)]
        assert codes == [200] * 5 + [429]

    def test_plain_scan_forwards_the_parent_link(self, client):
        client.post(
            "/api/username-search/scan",
            json={"username": "a", "parent_search_id": 3, "pivot_source": "p"},
        )
        assert client.calls[0]["parent_search_id"] == 3
        assert client.calls[0]["pivot_source"] == "p"
