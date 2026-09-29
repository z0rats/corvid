from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.git_recon.models.git_recon_models import GitReconSearch

# No completed_at column and an error column named `error`; results are a JSON blob
# column, not a child table (see ADR-0002), so there's no `relation` to eager-load.
GIT_RECON_SCANS = ScanFeature(
    name="git_recon",
    model=GitReconSearch,
    columns=ScanColumns(error_column="error", completed_at_column=None),
    order_by=GitReconSearch.searched_at,
)
