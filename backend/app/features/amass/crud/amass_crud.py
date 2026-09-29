from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.amass.models.amass_models import AmassSearch

# No completed_at column and an error column named `error`; results are a JSON blob
# column rather than a child table (no `relation`) - same shape as GitReconSearch.
AMASS_SCANS = ScanFeature(
    name="amass",
    model=AmassSearch,
    columns=ScanColumns(error_column="error", completed_at_column=None),
    order_by=AmassSearch.searched_at,
)
