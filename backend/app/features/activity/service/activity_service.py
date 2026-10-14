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


async def _non_scan_activity(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    """Histories that aren't `ScanFeature`s (no running/failed lifecycle - always completed)."""
    sources: list[tuple[str, Any, Any, Any]] = [
        ("ioc_lookup", SingleLookupSearch, SingleLookupSearch.ioc, SingleLookupSearch.searched_at),
        ("reddit_search", RedditSearch, RedditSearch.username, RedditSearch.searched_at),
    ]
    items: list[dict[str, Any]] = []
    for feature, model, target, timestamp in sources:
        rows = await db.execute(
            select(model.id, target, timestamp).order_by(timestamp.desc()).limit(limit)
        )
        items.extend(
            {"feature": feature, "id": id_, "target": value, "status": "completed", "timestamp": ts}
            for id_, value, ts in rows.all()
        )
    return items


async def list_recent_activity(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    items = await _non_scan_activity(db, limit)
    for feature in all_scan_features():
        items.extend(await feature.recent_activity(db, limit))
    for item in items:
        item["timestamp"] = _as_utc(item["timestamp"])
    items.sort(key=lambda item: item["timestamp"], reverse=True)
    return items[:limit]
