"""CRUD operations for trends blacklist entries"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.newsfeed.models.newsfeed_models import TrendsBlacklistEntry


async def get_blacklist_entries(db: AsyncSession, entry_type: str | None = None) -> list[TrendsBlacklistEntry]:
    """Retrieve blacklist entries, optionally filtered by type"""
    stmt = select(TrendsBlacklistEntry)
    if entry_type:
        stmt = stmt.where(TrendsBlacklistEntry.type == entry_type)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_blacklist_values(db: AsyncSession, entry_type: str) -> set[str]:
    """Retrieve the set of blacklisted values for a given type (for fast filtering)"""
    stmt = select(TrendsBlacklistEntry.value).where(TrendsBlacklistEntry.type == entry_type)
    result = await db.execute(stmt)
    return {row[0] for row in result.all()}


async def create_blacklist_entry(db: AsyncSession, value: str, entry_type: str) -> TrendsBlacklistEntry:
    """Create a new blacklist entry"""
    entry = TrendsBlacklistEntry(value=value.strip().lower(), type=entry_type)
    db.add(entry)
    await db.flush()
    return entry


async def delete_blacklist_entry(db: AsyncSession, entry_id: int) -> bool:
    """Delete a blacklist entry by ID"""
    result = await db.execute(delete(TrendsBlacklistEntry).where(TrendsBlacklistEntry.id == entry_id))
    await db.flush()
    return result.rowcount > 0


async def blacklist_entry_exists(db: AsyncSession, value: str, entry_type: str) -> bool:
    """Check if a blacklist entry already exists"""
    stmt = select(TrendsBlacklistEntry).where(
        TrendsBlacklistEntry.value == value.strip().lower(),
        TrendsBlacklistEntry.type == entry_type,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
