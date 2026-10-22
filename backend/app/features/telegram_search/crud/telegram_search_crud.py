from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.features.telegram_search.models.telegram_search_models import TelegramChannelSearch

# No child-row table (see the model's docstring) - `relation` is left unset.
TELEGRAM_SEARCH_SCANS = ScanFeature(
    name="telegram_search",
    model=TelegramChannelSearch,
    columns=ScanColumns(error_column="error_message", completed_at_column="completed_at"),
    order_by=TelegramChannelSearch.started_at,
    target_column="channel",
)
