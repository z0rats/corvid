"""Orchestrates one Telegram channel analytics run: read the `t.me/<name>` card, page backwards
through the `t.me/s/<name>` preview up to the sample size, then compute metrics and indicators -
all driven through the shared `ScanRun` lifecycle."""

import asyncio
import datetime
import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from app.core.external_sources.contract import SourceDriftError
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanCancelled, ScanEvent, ScanOutcome
from app.core.scans.sse import queue_sink
from app.features.telegram_search.config.telegram_search_config import PAGE_DELAY_SECONDS
from app.features.telegram_search.crud.telegram_search_crud import TELEGRAM_SEARCH_SCANS
from app.features.telegram_search.schemas.telegram_search_schemas import (
    ChannelProfile,
    ScanRequest,
    ScanResult,
)
from app.features.telegram_search.service.channel_metrics import (
    compute_metrics,
    extract_indicators,
    to_sampled_post,
    top_posts,
)
from app.features.telegram_search.service.tme_client import TelegramSourceError, TmeClient
from app.features.telegram_search.service.tme_parser import (
    ChannelProfile as ParsedProfile,
)
from app.features.telegram_search.service.tme_parser import (
    PreviewPost,
    parse_preview_page,
    parse_profile_page,
)

logger = logging.getLogger(__name__)

# The first post of every channel is the "Channel created" service message.
_FIRST_POST_ID = 1


class TelegramSearchError(Exception):
    """An expected, user-facing failure (no such channel, a user account) - the run ends
    `failed` with this message, warning-logged without a traceback."""


@dataclass
class _Sample:
    posts: list[PreviewPost] = field(default_factory=list)
    preview_available: bool = False
    created_at: datetime.datetime | None = None
    media_counters: dict[str, int] = field(default_factory=dict)


async def _sample_posts(
    client: TmeClient,
    channel: str,
    max_posts: int,
    sample: _Sample,
    on_progress: Callable[[dict], None],
) -> None:
    """Fills `sample` in place (so a cancelled run keeps what it read), newest page first."""
    before: int | None = None
    seen: set[int] = set()
    while len(sample.posts) < max_posts:
        html = await client.fetch_preview_page(channel, before)
        if html is None:
            return
        page = parse_preview_page(html)
        if before is None:
            sample.preview_available = True
            sample.media_counters = {
                k: v for k, v in page.counters.items() if k not in ("subscribers", "members")
            }
        for post in reversed(page.posts):
            if post.id == _FIRST_POST_ID and post.is_service:
                sample.created_at = post.date
            # Pages can overlap (a post published mid-scan shifts them), so dedupe by id.
            if post.is_service or post.id in seen or len(sample.posts) >= max_posts:
                continue
            seen.add(post.id)
            sample.posts.append(post)
        on_progress({"stage": "posts", "sampled": len(sample.posts), "target": max_posts})
        # A cursor that doesn't move back would loop forever on a malformed page.
        if page.older_cursor is None or (before is not None and page.older_cursor >= before):
            return
        before = page.older_cursor
        await asyncio.sleep(PAGE_DELAY_SECONDS)


async def _fetch_created_at(client: TmeClient, channel: str) -> datetime.datetime | None:
    """Date of post #1 ("Channel created"), one extra request. None when it was deleted."""
    html = await client.fetch_preview_page(channel, before=_FIRST_POST_ID + 1)
    if html is None:
        return None
    for post in parse_preview_page(html).posts:
        if post.id == _FIRST_POST_ID and post.is_service:
            return post.date
    return None


def _build_result(channel: str, profile: ParsedProfile, sample: _Sample) -> ScanResult:
    posts = sample.posts
    return ScanResult(
        profile=ChannelProfile(
            username=channel,
            url=f"https://t.me/{channel}",
            title=profile.title,
            kind="unknown" if profile.kind == "user" else profile.kind,
            member_count=profile.member_count,
            online_count=profile.online_count,
            description=profile.description,
            verified=profile.verified,
            photo_url=profile.photo_url,
            created_at=sample.created_at,
            preview_available=sample.preview_available,
            media_counters=sample.media_counters,
        ),
        metrics=(
            compute_metrics(posts, channel, profile.member_count)
            if sample.preview_available
            else None
        ),
        top_posts=top_posts(posts),
        posts=[to_sampled_post(p) for p in posts],
        indicators=extract_indicators(posts, profile.description),
    )


def _outcome(channel: str, profile: ParsedProfile, sample: _Sample) -> ScanOutcome:
    result = _build_result(channel, profile, sample)
    return ScanOutcome(
        fields={
            "title": profile.title,
            "kind": result.profile.kind,
            "member_count": profile.member_count,
            "posts_sampled": len(sample.posts),
        },
        db_only_fields={"result": result.model_dump(mode="json")},
    )


async def run_scan(request: ScanRequest, queue: asyncio.Queue) -> None:
    """Run one channel analytics scan as a detached task: it keeps running and persists its
    result even if the SSE client disconnects. Cancelling keeps the posts sampled so far."""
    on_event = queue_sink(queue)
    channel = request.channel

    async def run_work(search_id: int) -> ScanOutcome:
        def on_progress(data: dict) -> None:
            on_event(ScanEvent("progress", data))

        on_progress({"stage": "profile"})
        sample = _Sample()
        async with TmeClient() as client:
            profile = parse_profile_page(await client.fetch_profile_page(channel))
            if profile is None:
                raise TelegramSearchError(f"No public Telegram channel or group named @{channel}")
            if profile.kind == "user":
                raise TelegramSearchError(
                    f"@{channel} is a user or bot account, not a channel or group"
                )
            on_progress({"stage": "profile_done", "title": profile.title, "kind": profile.kind})

            try:
                await _sample_posts(client, channel, request.max_posts, sample, on_progress)
                if sample.preview_available and sample.created_at is None:
                    on_progress({"stage": "created"})
                    sample.created_at = await _fetch_created_at(client, channel)
            except asyncio.CancelledError:
                raise ScanCancelled(_outcome(channel, profile, sample)) from None

        on_progress({"stage": "analyzing"})
        return _outcome(channel, profile, sample)

    task = asyncio.current_task()
    assert task is not None, "run_scan runs as its own task (see the /scan route)"
    await TELEGRAM_SEARCH_SCANS.execute(
        run_work,
        on_event,
        create_fields={
            "target": request.target,
            "channel": channel,
            "max_posts": request.max_posts,
        },
        started_fields={"channel": channel},
        cancellable=TaskCancellable(task),
        expected_exceptions=(TelegramSearchError, TelegramSourceError, SourceDriftError),
    )
