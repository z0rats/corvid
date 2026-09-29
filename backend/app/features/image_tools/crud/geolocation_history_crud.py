from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.geolocation_history_models import ImageGeolocationSearch
from ..schemas.image_schemas import ImageGeolocationResponse


async def create_search(
    db: AsyncSession,
    filename: str,
    image_sha256: str,
    result: ImageGeolocationResponse,
) -> ImageGeolocationSearch:
    """Persist a completed AI geolocation analysis."""
    top = result.candidates[0] if result.candidates else None
    search = ImageGeolocationSearch(
        filename=filename,
        image_sha256=image_sha256,
        model_used=result.model_used,
        top_candidate=top.location if top else None,
        top_confidence=top.confidence if top else None,
        result=result.model_dump(mode="json", exclude={"model_used", "history_id"}),
    )
    db.add(search)
    await db.flush()
    await db.refresh(search)
    return search


async def list_searches(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[ImageGeolocationSearch]:
    """List past geolocation analyses, most recent first."""
    result = await db.execute(
        select(ImageGeolocationSearch)
        .order_by(ImageGeolocationSearch.searched_at.desc(), ImageGeolocationSearch.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_search(db: AsyncSession, search_id: int) -> ImageGeolocationSearch | None:
    """Get a past geolocation analysis by ID."""
    result = await db.execute(
        select(ImageGeolocationSearch).where(ImageGeolocationSearch.id == search_id)
    )
    return result.scalar_one_or_none()


async def delete_search(db: AsyncSession, search_id: int) -> ImageGeolocationSearch | None:
    """Delete a past geolocation analysis."""
    search = await get_search(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
