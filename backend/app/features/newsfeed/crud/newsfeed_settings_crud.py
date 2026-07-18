from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.features.newsfeed.models.newsfeed_models import NewsfeedSettings
from app.features.newsfeed.schemas.newsfeed_schemas import NewsfeedSettingsSchema
from app.features.newsfeed.utils.favicon_downloader import FaviconDownloader

logger = logging.getLogger(__name__)


def _active_feed_query():
    """Base query selecting only non-deleted feeds"""
    return select(NewsfeedSettings).where(NewsfeedSettings.deleted == False)  # noqa: E712


async def get_all_newsfeed_settings(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[NewsfeedSettings]:
    """Retrieve all active (non-deleted) newsfeed settings with pagination"""
    result = await db.execute(_active_feed_query().offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_newsfeed_setting(db: AsyncSession, settings: NewsfeedSettingsSchema) -> NewsfeedSettings:
    """Create a new newsfeed setting entry"""
    data = settings.model_dump()
    data["url"] = str(data["url"])
    db_settings = NewsfeedSettings(**data)
    db.add(db_settings)
    await db.flush()
    await db.refresh(db_settings)
    return db_settings


async def update_newsfeed_setting(db: AsyncSession, name: str, settings: NewsfeedSettingsSchema) -> NewsfeedSettings | None:
    """Update existing active newsfeed setting or create new one if not found"""
    result = await db.execute(_active_feed_query().where(NewsfeedSettings.name == name))
    db_settings = result.scalar_one_or_none()

    if db_settings:
        db_settings.name = settings.name
        db_settings.url = str(settings.url)
        db_settings.icon = settings.icon
        db_settings.enabled = settings.enabled
        await db.flush()
        await db.refresh(db_settings)
        return db_settings

    return await create_newsfeed_setting(db, settings)


async def delete_newsfeed_setting(db: AsyncSession, feed_name: str) -> bool:
    """Delete a newsfeed setting by name (soft-delete for defaults, hard-delete for custom)"""
    from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS

    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == feed_name))
    db_settings = result.scalar_one_or_none()

    if not db_settings:
        return False

    default_names = {feed["name"] for feed in DEFAULT_NEWSFEEDS}
    if feed_name in default_names:
        db_settings.deleted = True
        await db.flush()
    else:
        await db.delete(db_settings)
        await db.flush()

    return True


async def toggle_feed_status(db: AsyncSession, feed_name: str, enabled: bool) -> NewsfeedSettings | None:
    """Enable or disable an active newsfeed by name"""
    result = await db.execute(_active_feed_query().where(NewsfeedSettings.name == feed_name))
    setting = result.scalar_one_or_none()

    if not setting:
        return None

    setting.enabled = enabled
    await db.flush()
    await db.refresh(setting)
    return setting


async def create_custom_feed(db: AsyncSession, settings: NewsfeedSettingsSchema) -> NewsfeedSettings:
    """Create or update a custom newsfeed entry"""
    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == settings.name))
    existing_feed = result.scalar_one_or_none()

    if existing_feed:
        existing_feed.url = str(settings.url)
        existing_feed.icon = settings.icon
        existing_feed.enabled = bool(settings.enabled)
        await db.flush()
        await db.refresh(existing_feed)
        return existing_feed

    db_feed = NewsfeedSettings(
        name=settings.name,
        url=str(settings.url),
        icon=settings.icon,
        enabled=bool(settings.enabled),
    )
    db.add(db_feed)
    await db.flush()
    await db.refresh(db_feed)
    return db_feed


async def create_custom_feed_with_favicon(db: AsyncSession, settings: NewsfeedSettingsSchema) -> NewsfeedSettings:
    """Create or update a custom newsfeed entry with favicon download if no icon provided"""
    if not settings.icon or settings.icon == "default.png":
        logger.info("Attempting to download favicon for feed %s from %s", settings.name, settings.url)
        try:
            success, icon_filename, error = await FaviconDownloader.download_and_save_favicon(settings.url)
            if success and icon_filename:
                settings.icon = icon_filename
                settings.icon_id = icon_filename
                logger.info("Successfully downloaded favicon for %s: %s", settings.name, icon_filename)
            else:
                logger.warning("Failed to download favicon for %s: %s", settings.name, error or "Unknown error")
                settings.icon = "default.png"
                settings.icon_id = None
        except Exception as e:
            logger.warning("Exception during favicon download for %s: %s", settings.name, str(e))
            settings.icon = "default.png"
            settings.icon_id = None

    return await create_custom_feed(db, settings)


async def delete_custom_feed(db: AsyncSession, name: str) -> bool:
    """Delete a newsfeed entry by name (soft-delete for defaults, hard-delete for custom)"""
    from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS

    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == name))
    db_feed = result.scalar_one_or_none()

    if not db_feed:
        return False

    default_names = {feed["name"] for feed in DEFAULT_NEWSFEEDS}
    if name in default_names:
        db_feed.deleted = True
        await db.flush()
    else:
        await db.delete(db_feed)
        await db.flush()

    return True


async def record_feed_fetch_result(db: AsyncSession, feed_name: str, success: bool, error: str | None) -> None:
    """Record the outcome of a fetch attempt for a feed, so a persistently failing
    feed (bad URL, provider outage) surfaces to the user instead of only ever
    appearing in server logs."""
    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == feed_name))
    feed = result.scalar_one_or_none()
    if not feed:
        return

    feed.last_fetched_at = datetime.now(timezone.utc)
    if success:
        feed.last_success_at = feed.last_fetched_at
        feed.last_error = None
    else:
        feed.last_error = error[:500] if error else None
    await db.flush()


async def get_feed_by_name(db: AsyncSession, name: str) -> NewsfeedSettings | None:
    """Get a newsfeed setting by name, including soft-deleted feeds (needed for PK conflict checks)"""
    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == name))
    return result.scalar_one_or_none()


async def get_feeds_with_default_icon(db: AsyncSession) -> list[NewsfeedSettings]:
    """Retrieve all active feeds that are using the default icon"""
    result = await db.execute(
        _active_feed_query()
        .where(
            or_(
                NewsfeedSettings.icon == "default.png",
                NewsfeedSettings.icon_id == None,
            )
        )
    )
    return list(result.scalars().all())


async def update_feed_icon(db: AsyncSession, feed_name: str, icon_id: str) -> NewsfeedSettings | None:
    """Update the icon fields for an active feed by name"""
    result = await db.execute(_active_feed_query().where(NewsfeedSettings.name == feed_name))
    feed = result.scalar_one_or_none()

    if not feed:
        return None

    feed.icon = icon_id
    feed.icon_id = icon_id
    await db.flush()
    await db.refresh(feed)
    return feed
