import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult


async def create_search_run(db: AsyncSession, username: str) -> MailSearch:
    """Create a new search run in the 'running' state"""
    search = MailSearch(username=username, status="running")
    db.add(search)
    await db.flush()
    await db.refresh(search)
    return search


async def complete_search_run(
    db: AsyncSession,
    search_id: int,
    total_providers_checked: int,
    found_providers: list[dict],
) -> MailSearch | None:
    """Mark a search run as completed, storing its found-provider results"""
    search = await get_search_run(db, search_id)
    if not search:
        return None

    search.status = "completed"
    search.total_providers_checked = total_providers_checked
    search.found_count = len(found_providers)
    search.completed_at = datetime.datetime.now(datetime.timezone.utc)

    for provider in found_providers:
        db.add(MailSearchResult(
            search_id=search_id,
            provider_name=provider["provider_name"],
            emails=provider["emails"],
            extra=provider.get("extra"),
        ))

    await db.flush()
    return search


async def cancel_search_run(
    db: AsyncSession,
    search_id: int,
    total_providers_checked: int,
    found_providers: list[dict],
) -> MailSearch | None:
    """Mark a search run as cancelled, storing whatever found-provider results
    were captured before cancellation."""
    search = await get_search_run(db, search_id)
    if not search:
        return None

    search.status = "cancelled"
    search.total_providers_checked = total_providers_checked
    search.found_count = len(found_providers)
    search.completed_at = datetime.datetime.now(datetime.timezone.utc)

    for provider in found_providers:
        db.add(MailSearchResult(
            search_id=search_id,
            provider_name=provider["provider_name"],
            emails=provider["emails"],
            extra=provider.get("extra"),
        ))

    await db.flush()
    return search


async def fail_search_run(db: AsyncSession, search_id: int, error_message: str) -> MailSearch | None:
    """Mark a search run as failed"""
    search = await get_search_run(db, search_id)
    if not search:
        return None

    search.status = "failed"
    search.error_message = error_message[:1000]
    search.completed_at = datetime.datetime.now(datetime.timezone.utc)

    await db.flush()
    return search


async def list_search_runs(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[MailSearch]:
    """List past search runs, most recent first"""
    result = await db.execute(
        select(MailSearch).order_by(MailSearch.started_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_search_run(db: AsyncSession, search_id: int) -> MailSearch | None:
    """Get a search run by ID, without its provider results"""
    result = await db.execute(select(MailSearch).where(MailSearch.id == search_id))
    return result.scalar_one_or_none()


async def get_search_run_with_results(db: AsyncSession, search_id: int) -> MailSearch | None:
    """Get a search run by ID, including its found-provider results"""
    result = await db.execute(
        select(MailSearch)
        .where(MailSearch.id == search_id)
        .options(selectinload(MailSearch.provider_results))
    )
    return result.scalar_one_or_none()


async def delete_search_run(db: AsyncSession, search_id: int) -> MailSearch | None:
    """Delete a search run and its provider results"""
    search = await get_search_run(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
