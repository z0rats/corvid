"""Orchestrates a Steam Recon scan: resolve the target, collect its friends graph, rank close
friends by mutual-connection weight, aggregate a geolocation hypothesis, and (optionally) score
the CS2 cheater-probability report - all driven through the shared `ScanRun` lifecycle.
"""

import asyncio
import datetime
import logging

from app.core.database import managed_session
from app.core.exceptions import AppHTTPException
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanEvent, ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.features.steam_recon.config.steam_recon_config import (
    CLOSE_FRIENDS_TOP_N,
    build_quick_links,
)
from app.features.steam_recon.crud.steam_recon_crud import SCAN_COLUMNS
from app.features.steam_recon.models.steam_recon_models import SteamReconSearch
from app.features.steam_recon.schemas.steam_recon_schemas import (
    CheaterReport as CheaterReportSchema,
)
from app.features.steam_recon.schemas.steam_recon_schemas import (
    CheaterSignal,
    CloseFriend,
    GeolocationHypothesis,
    LocationCandidateSchema,
    QuickLink,
    ScanRequest,
    ScanResult,
    SteamLocation,
    SteamProfile,
)
from app.features.steam_recon.service.steam_api_client import SteamApiClient, SteamApiError
from app.features.steam_recon.service.steam_api_key_service import get_steam_api_key
from app.features.steam_recon.service.steam_cheater_scoring_service import compute_cheater_report
from app.features.steam_recon.service.steam_comments_service import (
    classify_accusatory_ratio,
    fetch_profile_comments,
)
from app.features.steam_recon.service.steam_geolocation_service import (
    LocationAggregate,
    aggregate_locations,
    resolve_hypothesis_names,
)
from app.features.steam_recon.service.steam_graph_service import (
    FriendCandidate,
    FriendsPrivateError,
    GraphResult,
    collect_friend_graph,
)
from app.features.steam_recon.service.steam_profile_service import (
    VISIBILITY_BY_STATE,
    map_bans,
    map_location,
    optional,
    resolve_steamid64,
)

logger = logging.getLogger(__name__)

FEATURE_NAME = "steam_recon"


class SteamReconError(Exception):
    """A scan-domain validation failure (bad target, unknown profile, no key configured) - an
    "expected" failure surfaced via the normal running -> failed transition (warning-logged, no
    traceback), not an application error."""


async def cancel_scan(search_id: int) -> bool:
    return await ScanRun.cancel(FEATURE_NAME, search_id)


async def _resolve_steamid64_for_scan(client: SteamApiClient, raw_target: str) -> str:
    """`resolve_steamid64` raises `AppHTTPException` for the /profile endpoint's direct HTTP
    contract - a scan instead surfaces it as a `SteamReconError` through the normal scan
    running -> failed transition."""
    try:
        return await resolve_steamid64(client, raw_target)
    except AppHTTPException as exc:
        raise SteamReconError(exc.detail) from exc


def _account_age_days(created_at: int | None) -> int | None:
    if not created_at:
        return None
    created = datetime.datetime.fromtimestamp(created_at, tz=datetime.UTC)
    return (datetime.datetime.now(datetime.UTC) - created).days


def _close_friend(candidate: FriendCandidate) -> CloseFriend:
    location = None
    if candidate.country_code:
        location = SteamLocation(
            country_code=candidate.country_code,
            state_code=candidate.state_code,
            city_id=candidate.city_id,
        )
    bans = candidate.bans or {}
    return CloseFriend(
        steamid64=candidate.steamid64,
        persona_name=candidate.persona_name,
        avatar_url=candidate.avatar_url,
        mutual_count=candidate.mutual_count,
        friend_since=candidate.friend_since,
        location=location,
        vac_banned=bool(bans.get("VACBanned")),
        game_banned=bool(bans.get("NumberOfGameBans", 0) > 0),
        friends_private=candidate.friends_private,
    )


def _geolocation_schema(aggregate: LocationAggregate, self_declared) -> GeolocationHypothesis:
    def _candidates(items):
        return [
            LocationCandidateSchema(code=c.code, name=c.name, weight=c.weight, share=c.share)
            for c in items
        ]

    return GeolocationHypothesis(
        confidence=aggregate.confidence,
        num_voters=aggregate.num_voters,
        coverage=aggregate.coverage,
        countries=_candidates(aggregate.countries),
        states=_candidates(aggregate.states),
        cities=_candidates(aggregate.cities),
        self_declared=self_declared,
    )


async def _build_cheater_report(
    client: SteamApiClient,
    steamid64: str,
    bans,
    graph: GraphResult,
    account_age_days: int | None,
    level: int | None,
    game_count: int | None,
) -> CheaterReportSchema:
    cs2_stats = await optional(client.get_cs2_stats(steamid64))
    comments = await fetch_profile_comments(steamid64)
    if comments:
        accusatory_ratio, sample_size = classify_accusatory_ratio(comments, steamid64)
    else:
        accusatory_ratio, sample_size = None, 0

    report = compute_cheater_report(
        bans=bans,
        candidates=graph.candidates,
        account_age_days=account_age_days,
        level=level,
        game_count=game_count,
        cs2_stats=cs2_stats,
        accusatory_ratio=accusatory_ratio,
        accusatory_sample_size=sample_size,
    )
    return CheaterReportSchema(
        probability=report.probability,
        level=report.level,
        coverage=report.coverage,
        already_banned=report.already_banned,
        signals=[
            CheaterSignal(
                id=s.id,
                value=s.value,
                weight=s.weight,
                contribution=s.contribution,
                explanation=s.explanation,
            )
            for s in report.signals
        ],
    )


async def run_scan(request: ScanRequest, queue: asyncio.Queue) -> None:
    """Run a full Steam Recon scan, persisting the result and streaming live progress.

    Runs independently of the SSE client's connection, same lifecycle as every other
    scan-style feature in this codebase - spawned as a background task, it keeps running and
    persists its result even if the client disconnects. Cancellable via `cancel_scan`.
    """
    on_event = queue_sink(queue)

    async def run_work(search_id: int) -> ScanOutcome:
        async with managed_session() as db:
            api_key = await get_steam_api_key(db)
        if not api_key:
            raise SteamReconError(
                "A Steam Web API key is required. Add one under Settings > API Keys."
            )

        def on_progress(stage: str, data: dict) -> None:
            on_event(ScanEvent("progress", {"stage": stage, **data}))

        on_progress("resolving", {})
        async with SteamApiClient(api_key) as client:
            steamid64 = await _resolve_steamid64_for_scan(client, request.target)

            summaries, bans_raw, level, game_count = await asyncio.gather(
                client.get_player_summaries([steamid64]),
                optional(client.get_player_bans([steamid64])),
                optional(client.get_steam_level(steamid64)),
                optional(client.get_owned_games_count(steamid64)),
            )
            summary = summaries.get(steamid64)
            if summary is None:
                raise SteamReconError("Steam returned no profile for this ID")

            bans = map_bans((bans_raw or {}).get(steamid64))
            location = await map_location(summary)

            try:
                graph = await collect_friend_graph(
                    client, steamid64, request.max_friends, on_progress
                )
            except FriendsPrivateError as exc:
                raise SteamReconError(str(exc)) from exc

            on_progress("scoring", {})
            aggregate = await resolve_hypothesis_names(aggregate_locations(graph.candidates))

            cheater_report = None
            if request.include_cs_report:
                cheater_report = await _build_cheater_report(
                    client,
                    steamid64,
                    bans,
                    graph,
                    _account_age_days(summary.get("timecreated")),
                    level,
                    game_count,
                )

        profile = SteamProfile(
            steamid64=steamid64,
            persona_name=summary.get("personaname"),
            real_name=summary.get("realname"),
            profile_url=summary.get("profileurl"),
            avatar_url=summary.get("avatarfull"),
            visibility=VISIBILITY_BY_STATE.get(
                summary.get("communityvisibilitystate", 0), "unknown"
            ),
            created_at=summary.get("timecreated"),
            last_logoff=summary.get("lastlogoff"),
            location=location,
            level=level,
            game_count=game_count,
            bans=bans,
        )
        result = ScanResult(
            profile=profile,
            quick_links=[QuickLink(**link) for link in build_quick_links(steamid64)],
            close_friends=[_close_friend(c) for c in graph.candidates[:CLOSE_FRIENDS_TOP_N]],
            geolocation=_geolocation_schema(aggregate, location),
            cheater_report=cheater_report,
        )

        fields = {
            "steamid64": steamid64,
            "persona_name": summary.get("personaname"),
            "friends_total": graph.friends_total,
            "friends_analyzed": graph.friends_analyzed,
            "friends_located": sum(1 for c in graph.candidates if c.country_code),
            "top_country_code": aggregate.countries[0].code if aggregate.countries else None,
            "cheater_probability": cheater_report.probability if cheater_report else None,
        }
        return ScanOutcome(fields=fields, db_only_fields={"result": result.model_dump(mode="json")})

    cancellable = TaskCancellable(asyncio.current_task())
    await ScanRun.execute(
        FEATURE_NAME,
        SteamReconSearch,
        run_work,
        on_event,
        columns=SCAN_COLUMNS,
        create_fields={
            "target": request.target,
            "max_friends": request.max_friends,
            "include_cs_report": request.include_cs_report,
        },
        cancellable=cancellable,
        expected_exceptions=(SteamApiError, SteamReconError),
    )
