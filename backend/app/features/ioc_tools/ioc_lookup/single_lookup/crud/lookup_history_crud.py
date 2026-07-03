from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupResult,
    SingleLookupSearch,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.schemas.lookup_history_schemas import LookupResultCreate


async def create_search(
    db: AsyncSession, ioc: str, ioc_type: str, results: list[LookupResultCreate]
) -> SingleLookupSearch:
    """Persist a completed single-IOC lookup search with its per-service results"""
    search = SingleLookupSearch(ioc=ioc, ioc_type=ioc_type)
    db.add(search)
    await db.flush()

    for result in results:
        db.add(SingleLookupResult(
            search_id=search.id,
            service_key=result.service_key,
            service_name=result.service_name,
            status=result.status,
            summary=result.summary[:500],
            tlp=result.tlp,
            data=result.data,
        ))

    await db.flush()
    await db.refresh(search)
    return search


async def list_searches(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[SingleLookupSearch]:
    """List past search runs, most recent first"""
    result = await db.execute(
        select(SingleLookupSearch).order_by(SingleLookupSearch.searched_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_search(db: AsyncSession, search_id: int) -> SingleLookupSearch | None:
    """Get a search run by ID, without its results"""
    result = await db.execute(select(SingleLookupSearch).where(SingleLookupSearch.id == search_id))
    return result.scalar_one_or_none()


async def get_search_with_results(db: AsyncSession, search_id: int) -> SingleLookupSearch | None:
    """Get a search run by ID, including its per-service results"""
    result = await db.execute(
        select(SingleLookupSearch)
        .where(SingleLookupSearch.id == search_id)
        .options(selectinload(SingleLookupSearch.results))
    )
    return result.scalar_one_or_none()


async def delete_search(db: AsyncSession, search_id: int) -> SingleLookupSearch | None:
    """Delete a search run and its results"""
    search = await get_search(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
