import asyncio

import httpx
import pytest

from app.features.steam_recon.service import steam_locations_service

COUNTRIES = [
    {"countrycode": "RU", "hasstates": 1, "countryname": "Russia"},
    {"countrycode": "CC", "hasstates": 0, "countryname": "Cocos (Keeling) Islands"},
]
STATES = [{"countrycode": "RU", "statecode": "48", "statename": "Moscow"}]
CITIES = [
    {"countrycode": "RU", "statecode": "48", "cityid": 41460, "cityname": "Moscow"},
    {"countrycode": "RU", "statecode": "48", "cityid": 40677, "cityname": "Khimki"},
]


@pytest.fixture
def fake_steam(monkeypatch):
    """Route the service's httpx client to an in-memory handler and record requested paths."""
    steam_locations_service._cache.clear()
    steam_locations_service._locks.clear()
    paths: list[str] = []
    bodies = {
        "/actions/QueryLocations": COUNTRIES,
        "/actions/QueryLocations/RU": STATES,
        "/actions/QueryLocations/RU/48": CITIES,
        "/actions/QueryLocations/CC": None,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path not in bodies:
            return httpx.Response(400)
        return httpx.Response(200, json=bodies[request.url.path])

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        steam_locations_service.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
    )
    return paths


def _resolve(*args):
    return asyncio.run(steam_locations_service.resolve_location_names(*args))


def test_resolves_country_state_and_city(fake_steam):
    assert _resolve("RU", "48", 41460) == {"country": "Russia", "state": "Moscow", "city": "Moscow"}


def test_no_country_code_makes_no_requests(fake_steam):
    assert _resolve(None, "48", 41460) == {"country": None, "state": None, "city": None}
    assert fake_steam == []


def test_country_only_does_not_look_up_states_or_cities(fake_steam):
    assert _resolve("RU", None, None) == {"country": "Russia", "state": None, "city": None}
    assert fake_steam == ["/actions/QueryLocations"]


def test_country_without_states_yields_null_body_as_no_names(fake_steam):
    assert _resolve("CC", "01", 5) == {
        "country": "Cocos (Keeling) Islands",
        "state": None,
        "city": None,
    }


def test_unknown_city_id_leaves_city_unresolved(fake_steam):
    assert _resolve("RU", "48", 1)["city"] is None


def test_lookups_are_cached(fake_steam):
    _resolve("RU", "48", 41460)
    first_round = len(fake_steam)
    _resolve("RU", "48", 40677)
    assert len(fake_steam) == first_round


def test_concurrent_lookups_share_one_fetch(fake_steam):
    async def go():
        return await asyncio.gather(
            *(steam_locations_service.resolve_location_names("RU", "48", 41460) for _ in range(20))
        )

    results = asyncio.run(go())

    assert all(r["city"] == "Moscow" for r in results)
    assert sorted(fake_steam) == [
        "/actions/QueryLocations",
        "/actions/QueryLocations/RU",
        "/actions/QueryLocations/RU/48",
    ]


def test_http_failure_returns_no_names_and_is_not_cached(monkeypatch):
    steam_locations_service._cache.clear()
    steam_locations_service._locks.clear()
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        steam_locations_service.httpx,
        "AsyncClient",
        lambda **kw: real_client(
            transport=httpx.MockTransport(lambda r: httpx.Response(503)), **kw
        ),
    )

    assert _resolve("RU", "48", 41460) == {"country": None, "state": None, "city": None}
    assert steam_locations_service._cache == {}
