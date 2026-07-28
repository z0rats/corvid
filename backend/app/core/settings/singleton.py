from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


async def get_or_create_singleton(
    db: AsyncSession,
    model: type[ModelT],
    defaults: dict | None = None,
) -> ModelT:
    """Fetch the single row of `model`, creating one with `defaults` if none exists."""
    result = await db.execute(select(model).limit(1))
    instance = result.scalar_one_or_none()
    if instance is None:
        instance = model(**(defaults or {}))
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
    return instance
