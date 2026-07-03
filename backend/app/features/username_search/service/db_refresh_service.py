import asyncio
import logging

from maigret.db_updater import DEFAULT_META_URL, force_update, resolve_db_path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import managed_session
from app.core.settings.username_search.crud.username_search_settings_crud import record_db_refresh
from app.features.username_search.config.maigret_config import reload_maigret_database

logger = logging.getLogger(__name__)


async def refresh_database(db: AsyncSession | None = None, *, force: bool = False, check_interval_hours: int = 24) -> int:
    """Check for (or force) a Maigret site-database update and reload the in-process cache.

    Maigret's updater (`db_updater.resolve_db_path`/`force_update`) uses the
    synchronous `requests` library, so the network/disk work runs in a thread
    to avoid blocking the event loop. `resolve_db_path` already no-ops
    internally when `check_interval_hours` hasn't elapsed yet, so it's safe
    to call on every scheduled tick.

    Returns the number of sites in the (possibly just-updated) database.
    """
    if force:
        await asyncio.to_thread(force_update, DEFAULT_META_URL, False)
    else:
        await asyncio.to_thread(
            resolve_db_path, "resources/data.json", False, DEFAULT_META_URL, check_interval_hours, False
        )

    reloaded_db = reload_maigret_database()
    site_count = len(reloaded_db.sites)

    if db is not None:
        await record_db_refresh(db, site_count)
    else:
        async with managed_session() as session:
            await record_db_refresh(session, site_count)

    logger.info("Maigret site database refresh complete: %s sites loaded", site_count)
    return site_count
