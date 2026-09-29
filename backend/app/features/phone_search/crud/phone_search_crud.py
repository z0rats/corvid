from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.phone_search.models.phone_search_models import PhoneSearch, PhoneSearchResult

PHONE_SEARCH_SCANS = ScanFeature(
    name="phone_search",
    model=PhoneSearch,
    columns=ScanColumns(error_column="error_message", completed_at_column="completed_at"),
    order_by=PhoneSearch.started_at,
    relation=PhoneSearch.provider_results,
)


async def add_provider_results(
    db: AsyncSession, search_id: int, found_providers: list[dict]
) -> None:
    """Persist found-provider child rows for a search run. Called by run_work
    once it has results (on both normal completion and mid-scan cancellation) -
    ScanRun's generic mark_completed/mark_cancelled only ever touch scalar
    columns on the parent row, never these child rows."""
    for provider in found_providers:
        db.add(
            PhoneSearchResult(
                search_id=search_id,
                provider_name=provider["provider_name"],
                extra=provider.get("extra"),
            )
        )
    await db.flush()
