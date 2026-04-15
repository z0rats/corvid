from datetime import datetime, timezone

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.alerts_models import Alert


async def get_all_alerts(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Alert]:
    """Retrieve all alerts from the database with pagination"""
    result = await db.execute(
        select(Alert).order_by(Alert.timestamp.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_alert_by_id(db: AsyncSession, alert_id: int) -> Alert | None:
    """Retrieve a specific alert by ID"""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    return result.scalar_one_or_none()


async def get_alerts_by_module(db: AsyncSession, module: str, skip: int = 0, limit: int = 100) -> list[Alert]:
    """Retrieve alerts for a specific module with pagination"""
    result = await db.execute(
        select(Alert)
        .where(Alert.module == module)
        .order_by(Alert.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_alert(db: AsyncSession, module: str, title: str, message: str) -> Alert:
    """Create a new alert"""
    new_alert = Alert(
        module=module,
        title=title,
        message=message,
        read=False
    )
    db.add(new_alert)
    await db.flush()
    return new_alert


async def update_alert_read_status(db: AsyncSession, alert_id: int, read: bool) -> Alert | None:
    """Update the read status of an alert"""
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        return None

    alert.read = read
    if read and not alert.timestamp_read:
        alert.timestamp_read = datetime.now(timezone.utc)
    elif not read:
        alert.timestamp_read = None

    await db.flush()
    return alert


async def bulk_mark_all_alerts_read(db: AsyncSession) -> int:
    """Mark all unread alerts as read in a single query"""
    result = await db.execute(
        update(Alert)
        .where(Alert.read.is_(False))
        .values(read=True, timestamp_read=datetime.now(timezone.utc))
        .execution_options(synchronize_session=False)
    )
    await db.flush()
    return result.rowcount


async def delete_alert_by_id(db: AsyncSession, alert_id: int) -> Alert | None:
    """Delete a specific alert"""
    alert = await get_alert_by_id(db, alert_id)
    if not alert:
        return None

    await db.delete(alert)
    await db.flush()
    return alert


async def bulk_delete_all_alerts(db: AsyncSession) -> int:
    """Delete all alerts in a single query"""
    result = await db.execute(delete(Alert).execution_options(synchronize_session=False))
    await db.flush()
    return result.rowcount


async def count_unread_alerts(db: AsyncSession) -> int:
    """Count the number of unread alerts"""
    result = await db.execute(
        select(func.count()).select_from(Alert).where(Alert.read.is_(False))
    )
    return result.scalar_one()
