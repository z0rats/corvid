import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.investigations.models.investigation_models import (
    Investigation,
    InvestigationItem,
)


async def create_investigation(db: AsyncSession, name: str, notes: str | None) -> Investigation:
    investigation = Investigation(name=name, notes=notes)
    db.add(investigation)
    await db.flush()
    await db.refresh(investigation)
    return investigation


async def list_investigations(db: AsyncSession) -> list[tuple[Investigation, int]]:
    """Every investigation with its item count, most recently updated first."""
    result = await db.execute(
        select(Investigation, func.count(InvestigationItem.id))
        .outerjoin(InvestigationItem, InvestigationItem.investigation_id == Investigation.id)
        .group_by(Investigation.id)
        .order_by(Investigation.updated_at.desc(), Investigation.id.desc())
    )
    return [(row[0], row[1]) for row in result.all()]


async def get_investigation(db: AsyncSession, investigation_id: int) -> Investigation | None:
    """An investigation with its items loaded."""
    result = await db.execute(
        select(Investigation)
        .where(Investigation.id == investigation_id)
        .options(selectinload(Investigation.items))
    )
    return result.scalar_one_or_none()


async def delete_investigation(db: AsyncSession, investigation: Investigation) -> None:
    await db.delete(investigation)
    await db.flush()


async def find_item(
    db: AsyncSession, investigation_id: int, feature: str, run_id: int
) -> InvestigationItem | None:
    result = await db.execute(
        select(InvestigationItem).where(
            InvestigationItem.investigation_id == investigation_id,
            InvestigationItem.feature == feature,
            InvestigationItem.run_id == run_id,
        )
    )
    return result.scalar_one_or_none()


async def get_item(
    db: AsyncSession, investigation_id: int, item_id: int
) -> InvestigationItem | None:
    result = await db.execute(
        select(InvestigationItem).where(
            InvestigationItem.investigation_id == investigation_id,
            InvestigationItem.id == item_id,
        )
    )
    return result.scalar_one_or_none()


async def add_item(
    db: AsyncSession,
    investigation: Investigation,
    feature: str,
    run_id: int,
    target: str,
    note: str | None,
) -> InvestigationItem:
    item = InvestigationItem(
        investigation_id=investigation.id,
        feature=feature,
        run_id=run_id,
        target=target[:2000],
        note=note,
    )
    db.add(item)
    touch(investigation)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, investigation: Investigation, item: InvestigationItem):
    await db.delete(item)
    touch(investigation)
    await db.flush()


async def list_memberships(
    db: AsyncSession, feature: str, run_id: int
) -> list[tuple[Investigation, int]]:
    """Investigations that already hold this run, each with its (whole) item count."""
    holding = select(InvestigationItem.investigation_id).where(
        InvestigationItem.feature == feature, InvestigationItem.run_id == run_id
    )
    result = await db.execute(
        select(Investigation, func.count(InvestigationItem.id))
        .join(InvestigationItem, InvestigationItem.investigation_id == Investigation.id)
        .where(Investigation.id.in_(holding))
        .group_by(Investigation.id)
        .order_by(Investigation.name)
    )
    return [(row[0], row[1]) for row in result.all()]


def touch(investigation: Investigation) -> None:
    """Bump `updated_at` on an item change too, so the list's "recently updated" order holds -
    `onupdate` only fires when a column of the investigation row itself changes."""
    investigation.updated_at = datetime.datetime.now(datetime.UTC)
