import asyncio
import io
import logging
import os

from PIL import Image
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

ICONS_DIR = "app/static/feedicons"


async def save_icon(icon_data: bytes, icon_id: str) -> tuple[bool, str | None]:
    """Save a processed icon file to the filesystem"""
    try:
        os.makedirs(ICONS_DIR, exist_ok=True)
        icon_id = icon_id if icon_id.endswith(".png") else f"{icon_id}.png"
        file_path = os.path.join(ICONS_DIR, icon_id)

        img = await asyncio.to_thread(Image.open, io.BytesIO(icon_data))

        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGB", img.size, "white")
            background.paste(img, mask=img.split()[-1])
            img = background

        await asyncio.to_thread(img.save, file_path, "PNG", optimize=True)
        logger.info("Successfully saved icon: %s", icon_id)
        return True, None

    except Exception as e:
        logger.error("Error saving icon: %s", str(e))
        return False, f"Error saving icon: {str(e)}"


def validate_icon_file(file_content: bytes, filename: str) -> tuple[bool, str | None]:
    """Validate icon file before processing"""
    MAX_FILE_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico"}

    if len(file_content) > MAX_FILE_SIZE:
        return False, f"File size too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)"

    file_extension = os.path.splitext(filename.lower())[1]
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    return True, None


def remove_existing_icon(icon_path: str) -> bool:
    """Remove existing icon file if it exists"""
    try:
        if os.path.exists(icon_path):
            os.remove(icon_path)
            logger.info("Removed existing icon file: %s", icon_path)
            return True
        return False
    except Exception as e:
        logger.warning("Failed to remove icon file %s: %s", icon_path, str(e))
        return False


def get_icon_path(icon_id: str) -> str:
    """Get full filesystem path for an icon file"""
    return os.path.join(ICONS_DIR, icon_id)


def icon_exists(icon_id: str) -> bool:
    """Check if an icon file exists"""
    return os.path.exists(get_icon_path(icon_id))


def get_default_icon_path() -> str:
    """Get path to the default icon"""
    return os.path.join(ICONS_DIR, "default.png")


def ensure_icons_directory() -> None:
    """Ensure icons directory exists"""
    os.makedirs(ICONS_DIR, exist_ok=True)


async def sync_article_icons(db, feed_name: str, new_icon: str) -> None:
    """Update the icon field on all articles belonging to a feed"""
    from app.features.newsfeed.models.newsfeed_models import NewsArticle

    result = await db.execute(
        update(NewsArticle)
        .where(NewsArticle.feedname == feed_name)
        .values(icon=new_icon)
    )
    logger.info("Updated icon to '%s' for %d articles of feed '%s'", new_icon, result.rowcount, feed_name)


async def delete_feed_icon(db, feed_name: str) -> tuple[bool, str]:
    """Delete a feed's icon file and reset it to the default icon"""
    from app.features.newsfeed.models.newsfeed_models import NewsfeedSettings, generate_icon_id

    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == feed_name))
    feed = result.scalar_one_or_none()

    if not feed:
        return False, "Feed not found"

    if feed.icon_id and feed.icon != "default.png":
        remove_existing_icon(get_icon_path(feed.icon_id))

    feed.icon = "default.png"
    feed.icon_id = generate_icon_id()
    await db.flush()
    await sync_article_icons(db, feed_name, "default.png")
    await db.flush()
    await db.refresh(feed)
    return True, "Icon deleted, using default icon"


async def bulk_fetch_favicons_parallel(db) -> None:
    """Fetch favicons for all feeds using the default icon, in parallel"""
    from app.features.newsfeed.crud.newsfeed_settings_crud import get_feeds_with_default_icon

    feeds = await get_feeds_with_default_icon(db)
    if not feeds:
        logger.info("No feeds with default icon found, skipping favicon fetch")
        return

    logger.info("Fetching favicons for %d feeds in parallel...", len(feeds))

    async def _fetch_single(feed_name: str) -> bool:
        try:
            success, _, _ = await refetch_feed_favicon(db, feed_name)
            return success
        except Exception as e:
            logger.error("Failed to fetch favicon for %s: %s", feed_name, e)
            return False

    results = await asyncio.gather(*[_fetch_single(feed.name) for feed in feeds])
    succeeded = sum(1 for r in results if r)
    logger.info("Favicon fetch complete: %d/%d succeeded", succeeded, len(feeds))


async def refetch_feed_favicon(db, feed_name: str) -> tuple[bool, str, str | None]:
    """Re-download the favicon for a feed, replacing any existing icon"""
    from app.features.newsfeed.models.newsfeed_models import NewsfeedSettings
    from app.features.newsfeed.utils.favicon_downloader import FaviconDownloader

    result = await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == feed_name))
    feed = result.scalar_one_or_none()

    if not feed:
        return False, "Feed not found", None

    if feed.icon_id and feed.icon != "default.png":
        remove_existing_icon(get_icon_path(feed.icon_id))

    logger.info("Refetching favicon for %s from %s", feed_name, feed.url)
    try:
        success, icon_filename, error = await FaviconDownloader.download_and_save_favicon(feed.url)
        if success and icon_filename:
            feed.icon = icon_filename
            feed.icon_id = icon_filename
            await sync_article_icons(db, feed_name, icon_filename)
            await db.flush()
            await db.refresh(feed)
            logger.info("Successfully refetched favicon for %s: %s", feed_name, icon_filename)
            return True, "Favicon downloaded successfully", icon_filename
        logger.warning("Failed to refetch favicon for %s: %s", feed_name, error)
        return False, f"Could not download favicon: {error or 'Unknown error'}", None
    except Exception as e:
        logger.error("Error refetching favicon for %s: %s", feed_name, str(e))
        return False, f"Error downloading favicon: {str(e)}", None
