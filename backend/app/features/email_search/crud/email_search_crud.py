from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult

EMAIL_SEARCH_SCANS = ScanFeature(
    name="email_search",
    model=MailSearch,
    columns=ScanColumns(error_column="error_message", completed_at_column="completed_at"),
    order_by=MailSearch.started_at,
    relation=MailSearch.provider_results,
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
            MailSearchResult(
                search_id=search_id,
                provider_name=provider["provider_name"],
                emails=provider["emails"],
                extra=provider.get("extra"),
            )
        )
    await db.flush()
