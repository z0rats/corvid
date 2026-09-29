import asyncio

from app.features.steam_recon.service.steam_geolocation_service import (
    aggregate_locations,
    resolve_hypothesis_names,
)
from app.features.steam_recon.service.steam_graph_service import FriendCandidate


def _candidate(steamid, mutual_count, country=None, state=None, city=None):
    return FriendCandidate(
        steamid64=steamid,
        persona_name=steamid,
        avatar_url=None,
        friend_since=None,
        country_code=country,
        state_code=state,
        city_id=city,
        mutual_count=mutual_count,
        friends_private=False,
        bans=None,
    )


def test_no_candidates_yields_low_confidence_empty_result():
    result = aggregate_locations([])

    assert result.confidence == "low"
    assert result.num_voters == 0
    assert result.countries == []


def test_candidates_without_any_connection_are_excluded_from_voting():
    candidates = [_candidate("A", 0, "US"), _candidate("B", 0, "RU")]

    result = aggregate_locations(candidates)

    assert result.num_voters == 0
    assert result.countries == []


def test_candidates_without_location_do_not_vote_but_still_lower_coverage():
    candidates = [_candidate("A", 5, "US"), _candidate("B", 5, None)]

    result = aggregate_locations(candidates)

    assert result.num_voters == 1
    assert result.coverage == 0.5
    assert result.countries[0].code == "US"


def test_country_ranking_is_weighted_by_mutual_count_not_raw_vote_count():
    candidates = [
        _candidate("A", 1, "RU"),
        _candidate("B", 1, "RU"),
        _candidate("C", 1, "RU"),
        _candidate("D", 10, "US"),
    ]

    result = aggregate_locations(candidates)

    assert result.countries[0].code == "US"
    assert result.countries[0].weight == 10
    assert result.countries[0].share == 10 / 13


def test_states_and_cities_are_scoped_to_the_leading_country():
    candidates = [
        _candidate("A", 5, "US", "WA", 100),
        _candidate("B", 3, "US", "WA", 200),
        _candidate("C", 1, "US", "CA", 300),
        _candidate("D", 20, "RU", "48", 400),  # bigger country weight, but not the leader
    ]
    # Make US the leading country by giving it more total weight than RU.
    candidates.append(_candidate("E", 25, "US", "WA", 100))

    result = aggregate_locations(candidates)

    assert result.countries[0].code == "US"
    assert {c.code for c in result.states} <= {"WA", "CA"}
    assert result.states[0].code == "WA"
    assert result.cities[0].code == "100"


def test_confidence_is_high_with_a_strong_majority_and_enough_voters():
    candidates = [_candidate(f"friend-{i}", 10, "US") for i in range(5)] + [
        _candidate("other", 1, "RU")
    ]

    result = aggregate_locations(candidates)

    assert result.confidence == "high"


def test_confidence_is_low_with_a_weak_split_even_with_many_voters():
    candidates = [_candidate(f"us-{i}", 1, "US") for i in range(3)] + [
        _candidate(f"ru-{i}", 1, "RU") for i in range(3)
    ]

    result = aggregate_locations(candidates)

    assert result.confidence == "low"


def test_resolve_hypothesis_names_fills_in_names(monkeypatch):
    import app.features.steam_recon.service.steam_geolocation_service as mod

    async def fake_resolve(country, state, city):
        return {
            "country": "United States" if country == "US" else None,
            "state": "Washington" if state == "WA" else None,
            "city": "Bellevue" if city == 100 else None,
        }

    monkeypatch.setattr(mod, "resolve_location_names", fake_resolve)
    aggregate = aggregate_locations([_candidate("A", 5, "US", "WA", 100)])

    resolved = asyncio.run(resolve_hypothesis_names(aggregate))

    assert resolved.countries[0].name == "United States"
    assert resolved.states[0].name == "Washington"
    assert resolved.cities[0].name == "Bellevue"
