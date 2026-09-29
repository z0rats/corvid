from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.steam_recon.models.steam_recon_models import SteamReconSearch

# No child-row table (see the model's docstring) - `relation` is left unset, same as git_recon.
STEAM_RECON_SCANS = ScanFeature(
    name="steam_recon",
    model=SteamReconSearch,
    columns=ScanColumns(error_column="error_message", completed_at_column="completed_at"),
    order_by=SteamReconSearch.started_at,
)
