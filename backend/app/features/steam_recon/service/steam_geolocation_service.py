"""Geolocation-by-social-graph: aggregates close friends' self-declared locations, weighted by
mutual-connection count, into a hierarchical country -> state -> city hypothesis for the target.

Pure aggregation (`aggregate_locations`) is separated from name resolution
(`resolve_hypothesis_names`, which calls the keyless `steam_locations_service`) so the ranking
logic is unit-testable with no network involved.
"""

import asyncio
import dataclasses

from app.features.steam_recon.config.steam_recon_config import (
    GEO_HIGH_CONFIDENCE_MIN_VOTERS,
    GEO_HIGH_CONFIDENCE_SHARE,
    GEO_MEDIUM_CONFIDENCE_MIN_VOTERS,
    GEO_MEDIUM_CONFIDENCE_SHARE,
    GEO_MIN_COVERAGE_FOR_MEDIUM,
    GEO_TOP_CANDIDATES_PER_LEVEL,
)
from app.features.steam_recon.service.steam_graph_service import FriendCandidate
from app.features.steam_recon.service.steam_locations_service import resolve_location_names


@dataclasses.dataclass
class LocationCandidate:
    code: str
    name: str | None
    weight: float
    share: float


@dataclasses.dataclass
class LocationAggregate:
    confidence: str  # "high" | "medium" | "low"
    num_voters: int
    coverage: float
    countries: list[LocationCandidate]
    states: list[LocationCandidate]  # within the leading country
    cities: list[LocationCandidate]  # within the leading state


def _rank(weights: dict[str, float], total: float) -> list[LocationCandidate]:
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    return [
        LocationCandidate(code=code, name=None, weight=weight, share=weight / total if total else 0)
        for code, weight in ranked[:GEO_TOP_CANDIDATES_PER_LEVEL]
    ]


def _confidence(
    leader_share: float, runner_up_share: float, num_voters: int, coverage: float
) -> str:
    # A tied (or near-tied) leader is excluded from both tiers below - "the top two countries
    # are effectively a coin flip" is never a confident hypothesis, however many voters there are.
    clear_leader = leader_share > runner_up_share
    if (
        clear_leader
        and leader_share >= GEO_HIGH_CONFIDENCE_SHARE
        and num_voters >= GEO_HIGH_CONFIDENCE_MIN_VOTERS
    ):
        return "high"
    if (
        clear_leader
        and leader_share >= GEO_MEDIUM_CONFIDENCE_SHARE
        and num_voters >= GEO_MEDIUM_CONFIDENCE_MIN_VOTERS
        and coverage >= GEO_MIN_COVERAGE_FOR_MEDIUM
    ):
        return "medium"
    return "low"


def aggregate_locations(candidates: list[FriendCandidate]) -> LocationAggregate:
    """Build the country/state/city hypothesis. `candidates` should be every analyzed friend
    (not just the top-20 close-friends list) - a friend with `mutual_count == 0` contributes no
    weight either way, so including them is harmless and keeps this function trusting its input
    rather than re-deriving what "analyzed" means."""
    connected = [c for c in candidates if c.mutual_count > 0]
    coverage = sum(1 for c in connected if c.country_code) / len(connected) if connected else 0.0

    voters = [c for c in connected if c.country_code]
    if not voters:
        return LocationAggregate(
            confidence="low", num_voters=0, coverage=coverage, countries=[], states=[], cities=[]
        )

    country_weights: dict[str, float] = {}
    for c in voters:
        assert c.country_code is not None  # guaranteed by the `voters` filter above
        country_weights[c.country_code] = country_weights.get(c.country_code, 0) + c.mutual_count
    total_weight = sum(country_weights.values())
    countries = _rank(country_weights, total_weight)
    leader_share = countries[0].share if countries else 0.0
    runner_up_share = countries[1].share if len(countries) > 1 else 0.0

    states: list[LocationCandidate] = []
    cities: list[LocationCandidate] = []
    if countries:
        leader_country = countries[0].code
        in_country = [c for c in voters if c.country_code == leader_country]

        state_weights: dict[str, float] = {}
        for c in in_country:
            if c.state_code:
                state_weights[c.state_code] = state_weights.get(c.state_code, 0) + c.mutual_count
        state_total = sum(state_weights.values())
        states = _rank(state_weights, state_total)

        if states:
            leader_state = states[0].code
            city_weights: dict[str, float] = {}
            for c in in_country:
                if c.state_code == leader_state and c.city_id:
                    key = str(c.city_id)
                    city_weights[key] = city_weights.get(key, 0) + c.mutual_count
            city_total = sum(city_weights.values())
            cities = _rank(city_weights, city_total)

    return LocationAggregate(
        confidence=_confidence(leader_share, runner_up_share, len(voters), coverage),
        num_voters=len(voters),
        coverage=coverage,
        countries=countries,
        states=states,
        cities=cities,
    )


async def resolve_hypothesis_names(aggregate: LocationAggregate) -> LocationAggregate:
    """Fill in `.name` for every candidate via the keyless location-name lookup."""
    country_code = aggregate.countries[0].code if aggregate.countries else None
    state_code = aggregate.states[0].code if aggregate.states else None

    async def resolve_country(candidate: LocationCandidate) -> LocationCandidate:
        names = await resolve_location_names(candidate.code, None, None)
        return dataclasses.replace(candidate, name=names["country"])

    async def resolve_state(candidate: LocationCandidate) -> LocationCandidate:
        names = await resolve_location_names(country_code, candidate.code, None)
        return dataclasses.replace(candidate, name=names["state"])

    async def resolve_city(candidate: LocationCandidate) -> LocationCandidate:
        names = await resolve_location_names(country_code, state_code, int(candidate.code))
        return dataclasses.replace(candidate, name=names["city"])

    countries, states, cities = await asyncio.gather(
        asyncio.gather(*(resolve_country(c) for c in aggregate.countries)),
        asyncio.gather(*(resolve_state(c) for c in aggregate.states)),
        asyncio.gather(*(resolve_city(c) for c in aggregate.cities)),
    )
    return dataclasses.replace(
        aggregate, countries=list(countries), states=list(states), cities=list(cities)
    )
