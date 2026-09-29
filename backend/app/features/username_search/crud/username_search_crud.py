from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.username_search.models.username_search_models import (
    MaigretSearch,
    MaigretSiteResult,
)

# Shared by all three username_search sources (maigret/social_analyzer/
# threat_actor_usernames all write this table); each passes its own alert
# `name` to `execute`, while cancel/history/reconciliation are per table.
USERNAME_SEARCH_SCANS = ScanFeature(
    name="username_search",
    model=MaigretSearch,
    columns=ScanColumns(error_column="error_message", completed_at_column="completed_at"),
    order_by=MaigretSearch.started_at,
    relation=MaigretSearch.site_results,
)


async def add_site_results(db: AsyncSession, search_id: int, found_sites: list[dict]) -> None:
    """Persist found-site child rows for a search run. Called by each source's
    own run_work once it has results (on both normal completion and mid-scan
    cancellation) - ScanRun's generic mark_completed/mark_cancelled only ever
    touch scalar columns on the parent row, never these child rows."""
    for site in found_sites:
        db.add(
            MaigretSiteResult(
                search_id=search_id,
                site_name=site["site_name"],
                url_user=site["url_user"],
                http_status=site.get("http_status"),
                extra=site.get("extra"),
            )
        )
    await db.flush()
