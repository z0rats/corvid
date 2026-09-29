"""Collects a target's friends graph and ranks friends by mutual-connection weight
("closeness"): `closeness(i) = |friends(i) ∩ friends(target)|`.

The expensive step is one `GetFriendList` call per candidate friend - candidates are capped
at `max_friends` (oldest `friend_since` first) before it runs, and fetched with bounded
concurrency plus a 429 retry, since a few hundred calls in quick succession routinely brushes
Steam's rate limit.
"""

import asyncio
import dataclasses
import logging
import math
from collections.abc import Callable, Coroutine
from typing import Any

from app.features.steam_recon.config.steam_recon_config import (
    FRIEND_FETCH_CONCURRENCY,
    FRIEND_FETCH_MAX_RETRIES,
    FRIEND_FETCH_RETRY_BACKOFF_SECONDS,
    VISIBILITY_PUBLIC,
)
from app.features.steam_recon.service.steam_api_client import SteamApiClient, SteamRateLimitedError

logger = logging.getLogger(__name__)


class FriendsPrivateError(Exception):
    """The target's own friend list is private - nothing to build a graph from."""


@dataclasses.dataclass
class FriendCandidate:
    steamid64: str
    persona_name: str | None
    avatar_url: str | None
    friend_since: int | None
    country_code: str | None
    state_code: str | None
    city_id: int | None
    mutual_count: int
    friends_private: bool
    bans: dict[str, Any] | None


@dataclasses.dataclass
class GraphResult:
    friends_total: int
    friends_analyzed: int
    candidates: list[FriendCandidate]


async def _retry_on_rate_limit[T](call: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """Retry `call` with backoff on a 429, honouring `Retry-After` when Steam sends one."""
    attempt = 0
    while True:
        try:
            return await call()
        except SteamRateLimitedError as exc:
            attempt += 1
            if attempt > FRIEND_FETCH_MAX_RETRIES:
                raise
            delay = exc.retry_after or FRIEND_FETCH_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
            logger.info("Steam rate limit hit, retrying in %.1fs (attempt %d)", delay, attempt)
            await asyncio.sleep(delay)


def select_candidates(
    friends: list[dict[str, Any]],
    summaries: dict[str, dict[str, Any]],
    max_friends: int,
) -> list[dict[str, Any]]:
    """Public friends only, oldest `friend_since` first (an older connection is more likely a
    genuinely close one), capped at `max_friends`. A missing `friend_since` sorts last."""
    public = [
        f
        for f in friends
        if summaries.get(f["steamid"], {}).get("communityvisibilitystate") == VISIBILITY_PUBLIC
    ]

    def sort_key(f: dict[str, Any]) -> float:
        friend_since = f.get("friend_since")
        return float(friend_since) if friend_since else math.inf

    public.sort(key=sort_key)
    return public[:max_friends]


async def _analyze_candidate(
    client: SteamApiClient,
    friend: dict[str, Any],
    summary: dict[str, Any],
    bans: dict[str, Any] | None,
    target_friend_ids: set[str],
) -> FriendCandidate:
    steamid = friend["steamid"]
    try:
        their_friends = await _retry_on_rate_limit(lambda: client.get_friend_list(steamid))
    except Exception:
        logger.warning("Failed to fetch friend list for %s, treating as private", steamid)
        their_friends = None

    if their_friends is None:
        mutual_count = 0
        friends_private = True
    else:
        their_ids = {f["steamid"] for f in their_friends}
        mutual_count = len(their_ids & target_friend_ids)
        friends_private = False

    return FriendCandidate(
        steamid64=steamid,
        persona_name=summary.get("personaname"),
        avatar_url=summary.get("avatarfull"),
        friend_since=friend.get("friend_since"),
        country_code=summary.get("loccountrycode"),
        state_code=summary.get("locstatecode"),
        city_id=summary.get("loccityid"),
        mutual_count=mutual_count,
        friends_private=friends_private,
        bans=bans,
    )


async def collect_friend_graph(
    client: SteamApiClient,
    target_steamid: str,
    max_friends: int,
    on_progress: Callable[[str, dict[str, Any]], None],
) -> GraphResult:
    """Fetch the target's friends, rank the (capped) public ones by mutual-connection weight.

    Raises:
        FriendsPrivateError: The target's friend list itself is private.
    """
    friends = await client.get_friend_list(target_steamid)
    if friends is None:
        raise FriendsPrivateError("This profile's friends list is private")

    target_friend_ids = {f["steamid"] for f in friends}
    on_progress("friends", {"friends_total": len(friends)})

    all_ids = list(target_friend_ids)
    summaries = await client.get_player_summaries(all_ids) if all_ids else {}
    candidates_raw = select_candidates(friends, summaries, max_friends)
    on_progress(
        "profiles", {"friends_total": len(friends), "candidates_selected": len(candidates_raw)}
    )

    bans_by_id = (
        await client.get_player_bans([c["steamid"] for c in candidates_raw])
        if candidates_raw
        else {}
    )

    semaphore = asyncio.Semaphore(FRIEND_FETCH_CONCURRENCY)
    analyzed = 0
    lock = asyncio.Lock()

    async def bounded_analyze(friend: dict[str, Any]) -> FriendCandidate:
        nonlocal analyzed
        async with semaphore:
            result = await _analyze_candidate(
                client,
                friend,
                summaries.get(friend["steamid"], {}),
                bans_by_id.get(friend["steamid"]),
                target_friend_ids,
            )
        async with lock:
            analyzed += 1
            on_progress(
                "mutual",
                {"analyzed": analyzed, "total": len(candidates_raw), "friends_total": len(friends)},
            )
        return result

    candidates: list[FriendCandidate] = await asyncio.gather(
        *(bounded_analyze(f) for f in candidates_raw)
    )
    candidates.sort(key=lambda c: c.mutual_count, reverse=True)

    return GraphResult(
        friends_total=len(friends),
        friends_analyzed=sum(1 for c in candidates if not c.friends_private),
        candidates=candidates,
    )
