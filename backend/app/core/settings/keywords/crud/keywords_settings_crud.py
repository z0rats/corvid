"""CRUD operations for keywords settings"""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.keywords.models.keywords_settings_models import Keyword


async def get_keywords_list(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Keyword]:
    """Retrieve keywords with pagination"""
    stmt = select(Keyword).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_keyword_by_id(db: AsyncSession, keyword_id: int) -> Keyword | None:
    """Retrieve a keyword by its ID"""
    stmt = select(Keyword).where(Keyword.id == keyword_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_keyword_by_value(db: AsyncSession, keyword_value: str) -> Keyword | None:
    """Retrieve a keyword by its value"""
    stmt = select(Keyword).where(Keyword.keyword == keyword_value.lower())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_keywords_count(db: AsyncSession) -> int:
    """Get total count of keywords"""
    stmt = select(func.count()).select_from(Keyword)
    result = await db.execute(stmt)
    return result.scalar_one()


async def create_keyword_record(db: AsyncSession, keyword_value: str) -> Keyword:
    """Create a new keyword record"""
    db_keyword = Keyword(keyword=keyword_value.lower())
    db.add(db_keyword)
    await db.flush()
    return db_keyword


async def update_keyword_record(db: AsyncSession, keyword: Keyword, new_value: str) -> Keyword:
    """Update an existing keyword record"""
    keyword.keyword = new_value.lower()
    await db.flush()
    return keyword


async def delete_keyword_record(db: AsyncSession, keyword_id: int) -> bool:
    """Delete a keyword record by ID"""
    result = await db.execute(delete(Keyword).where(Keyword.id == keyword_id))
    await db.flush()
    return result.rowcount > 0


async def keyword_exists(db: AsyncSession, keyword_value: str) -> bool:
    """Check if a keyword exists by value"""
    stmt = select(Keyword).where(Keyword.keyword == keyword_value.lower())
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def search_keywords(db: AsyncSession, search_term: str, skip: int = 0, limit: int = 100) -> list[Keyword]:
    """Search keywords by partial match"""
    search_pattern = f"%{search_term.lower()}%"
    stmt = (
        select(Keyword)
        .where(Keyword.keyword.like(search_pattern))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_keywords(db: AsyncSession) -> list[Keyword]:
    """Retrieve all keywords without pagination"""
    stmt = select(Keyword)
    result = await db.execute(stmt)
    return list(result.scalars().all())
