from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


async def get_or_create_singleton(
    db: AsyncSession,
    model: type[ModelT],
    defaults: dict | None = None,
) -> ModelT:
    """Fetch the single row of `model` (fixed id=1), creating one with `defaults` if none
    exists yet.

    Every caller's model documents its `id` column as "Singleton row id, always 1" but
    previously relied on autoincrement and a plain check-then-insert, so two concurrent
    first-requests could both see no row and both insert - racing on a shared connection
    could even tear down one insert mid-flight (`Could not refresh instance`), and even
    with isolated connections it would still silently create duplicate "singleton" rows.
    Forcing id=1 turns that race into a primary-key collision instead: the loser's insert
    fails atomically (rolled back via a savepoint, so it can't disturb anything else
    pending in the caller's session) and it just re-fetches the winner's row.
    """
    result = await db.execute(select(model).limit(1))
    instance = result.scalar_one_or_none()
    if instance is not None:
        return instance

    try:
        async with db.begin_nested():
            instance = model(id=1, **(defaults or {}))
            db.add(instance)
            await db.flush()
    except IntegrityError:
        result = await db.execute(select(model).limit(1))
        return result.scalar_one()

    await db.refresh(instance)
    return instance
