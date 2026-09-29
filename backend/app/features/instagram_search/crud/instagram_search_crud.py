from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.instagram_search.models.instagram_search_models import InstagramSearch

# Same shape as GitReconSearch: no completed_at column, error column named `error`,
# results a JSON blob column (see ADR-0002) rather than a child table.
INSTAGRAM_SCANS = ScanFeature(
    name="instagram_search",
    model=InstagramSearch,
    columns=ScanColumns(error_column="error", completed_at_column=None),
    order_by=InstagramSearch.searched_at,
)
