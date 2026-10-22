"""Cross-feature activity feed: the newest runs of every feature with a persisted history,
merged into one list - "what have I looked at recently" without opening each feature's own
history tab."""

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupSearch,
)
from app.features.reddit_search.models.reddit_search_models import RedditSearch
from app.utils.scan_reconciliation_registry import all_scan_features


def _as_utc(value: datetime.datetime) -> datetime.datetime:
    # SQLite hands back naive datetimes for timezone-aware columns; they're stored as UTC.
    return value if value.tzinfo else value.replace(tzinfo=datetime.UTC)


# Histories that aren't `ScanFeature`s (no running/failed lifecycle - always completed):
# (feature, model, target column, timestamp column).
_NON_SCAN_SOURCES: list[tuple[str, Any, Any, Any]] = [
    ("ioc_lookup", SingleLookupSearch, SingleLookupSearch.ioc, SingleLookupSearch.searched_at),
    ("reddit_search", RedditSearch, RedditSearch.username, RedditSearch.searched_at),
]


def activity_feature_names() -> list[str]:
    """Every feature name the feed can return - what investigations' run-source gate checks."""
    return [feature.name for feature in all_scan_features()] + [
        feature for feature, *_ in _NON_SCAN_SOURCES
    ]


async def _non_scan_activity(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for feature, model, target, timestamp in _NON_SCAN_SOURCES:
        rows = await db.execute(
            select(model.id, target, timestamp).order_by(timestamp.desc()).limit(limit)
        )
        items.extend(
            {"feature": feature, "id": id_, "target": value, "status": "completed", "timestamp": ts}
            for id_, value, ts in rows.all()
        )
    return items


async def list_active_runs(db: AsyncSession) -> list[dict[str, Any]]:
    """Every scan still running or queued, across all features, newest first - unbounded by
    recency, unlike the feed below, so a long-running scan never drops out of view."""
    items: list[dict[str, Any]] = []
    for feature in all_scan_features():
        items.extend(await feature.active_runs(db))
    for item in items:
        item["timestamp"] = _as_utc(item["timestamp"])
    items.sort(key=lambda item: item["timestamp"], reverse=True)
    return items


async def list_recent_activity(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    items = await _non_scan_activity(db, limit)
    for feature in all_scan_features():
        items.extend(await feature.recent_activity(db, limit))
    for item in items:
        item["timestamp"] = _as_utc(item["timestamp"])
    items.sort(key=lambda item: item["timestamp"], reverse=True)
    return items[:limit]
