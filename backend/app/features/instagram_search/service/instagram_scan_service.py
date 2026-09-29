"""Phase 2 - a followers/followees/posts scan of an Instagram profile, persisted
via `core/scans` (SSE-streamed, cancellable, history-backed), unlike Phase 1's
ephemeral single profile-metadata lookup.

`followers`/`followees` need a configured session - Instaloader's
`Profile.get_followers()`/`get_followees()` raise `LoginRequiredException`
immediately if the context isn't logged in, regardless of the target profile's
own privacy setting. `posts` works in both modes.

Instaloader's iteration is a blocking generator (`NodeIterator`, backed by
`requests`), so the whole scan runs inside one `asyncio.to_thread` worker and
checks `CooperativeCancellable`'s flag *and* a wall-clock deadline between
items - not just between pages - stopping early (partial results, `truncated:
True`) rather than walking an arbitrarily large list. `SCAN_MAX_ITEMS` is a
third, independent stop condition on top of those two.
"""

import asyncio
import logging
import threading
import time
from typing import Any

import instaloader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.core.scans.cancellable import CooperativeCancellable
from app.core.scans.run import ScanCancelled, ScanOutcome
from app.core.scans.sse import queue_sink
from app.features.instagram_search.config.instagram_search_config import (
    SCAN_MAX_ITEMS,
    SCAN_WALL_CLOCK_TIMEOUT_SECONDS,
    SESSION_OWNER_PLACEHOLDER,
)
from app.features.instagram_search.crud.instagram_search_crud import INSTAGRAM_SCANS
from app.features.instagram_search.service.instagram_common import (
    build_loader,
    raise_mapped_instaloader_exception,
)
from app.features.instagram_search.service.instagram_session_service import get_session_dict

logger = logging.getLogger(__name__)


def _map_follow_item(profile: instaloader.Profile) -> dict[str, Any]:
    # Only fields already present on the followers/followees edge list itself -
    # `username`/`full_name` read straight from the node, no per-item network call.
    return {"username": profile.username, "full_name": profile.full_name}


def _map_post_item(post: instaloader.Post) -> dict[str, Any]:
    caption = post.caption or ""
    return {
        "shortcode": post.shortcode,
        "permalink": f"https://www.instagram.com/p/{post.shortcode}/",
        "date_utc": post.date_utc.isoformat(),
        "is_video": post.is_video,
        "likes": post.likes,
        "comments": post.comments,
        "caption": caption[:500] or None,
    }


def _iterator_for(scan_type: str, profile: instaloader.Profile):
    if scan_type == "followers":
        return profile.get_followers(), _map_follow_item
    if scan_type == "followees":
        return profile.get_followees(), _map_follow_item
    return profile.get_posts(), _map_post_item


def _scan_sync(
    scan_type: str,
    username: str,
    session_data: dict[str, str] | None,
    stop_event: threading.Event,
    deadline: float,
) -> dict[str, Any]:
    """Blocking Instaloader iteration - runs off the event loop via `asyncio.to_thread`."""
    loader = build_loader()
    if session_data:
        loader.context.load_session(SESSION_OWNER_PLACEHOLDER, session_data)

    profile = instaloader.Profile.from_username(loader.context, username)
    iterator, mapper = _iterator_for(scan_type, profile)

    items: list[dict[str, Any]] = []
    truncated = False
    for node in iterator:
        if stop_event.is_set() or time.monotonic() > deadline:
            truncated = True
            break
        items.append(mapper(node))
        if len(items) >= SCAN_MAX_ITEMS:
            truncated = True
            break

    total_count: int | None = None
    try:
        total_count = iterator.count
    except Exception:  # noqa: BLE001 - best-effort enrichment, never worth failing the scan for
        logger.debug("Could not read total count for %s's %s", username, scan_type)
    if total_count is not None and total_count > len(items):
        truncated = True

    return {"items": items, "total_count": total_count, "truncated": truncated}


async def run_scan_task(
    *, username: str, scan_type: str, db: AsyncSession, queue: asyncio.Queue
) -> None:
    """Run one Instagram scan, persisting its result and streaming started/
    completed/cancelled/failed events via the given queue. Spawned as a
    background task by the route handler so the request isn't held open for
    the scan's full duration."""
    on_event = queue_sink(queue)
    session_data = await get_session_dict(db)
    mode = "session" if session_data else "anonymous"

    cancellable = CooperativeCancellable()
    deadline = time.monotonic() + SCAN_WALL_CLOCK_TIMEOUT_SECONDS

    async def run_work(search_id: int) -> ScanOutcome:
        try:
            result = await asyncio.to_thread(
                _scan_sync, scan_type, username, session_data, cancellable.stop_event, deadline
            )
        except instaloader.exceptions.InstaloaderException as e:
            raise_mapped_instaloader_exception(e, username)

        items = result["items"]
        logger.info(
            "Instagram %s scan for '%s': %d item(s) (truncated=%s, mode=%s)",
            scan_type,
            username,
            len(items),
            result["truncated"],
            mode,
        )
        outcome = ScanOutcome(
            fields={
                "item_count": len(items),
                "total_count": result["total_count"],
                "truncated": result["truncated"],
            },
            db_only_fields={"result": items},
        )
        if cancellable.stop_event.is_set():
            raise ScanCancelled(outcome)
        return outcome

    await INSTAGRAM_SCANS.execute(
        run_work,
        on_event,
        create_fields={"scan_type": scan_type, "username": username, "mode": mode},
        started_fields={"scan_type": scan_type, "username": username, "mode": mode},
        cancellable=cancellable,
        # raise_mapped_instaloader_exception always raises an AppHTTPException for a
        # library failure (login required, rate-limited, profile not found, ...) - all
        # routine, user-facing outcomes, not application bugs worth an error-level traceback.
        expected_exceptions=(AppHTTPException,),
    )
