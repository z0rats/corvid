from app.core.run_sources.source import RunSource
from app.features.email_search.service.run_source import EMAIL_SEARCH_RUN_SOURCE
from app.features.ioc_tools.ioc_lookup.single_lookup.service.run_source import (
    IOC_LOOKUP_RUN_SOURCE,
)
from app.features.reddit_search.service.run_source import REDDIT_SEARCH_RUN_SOURCE
from app.features.username_search.service.run_source import USERNAME_SEARCH_RUN_SOURCE

# Every feature whose runs can be added to an investigation, keyed by its activity-feed name.
# The only place allowed to know about all of them at once (same pattern as
# scan_reconciliation_registry.py). tests/core/test_run_source_coverage.py fails on a feature
# with a saved history that is in neither this dict nor RUN_SOURCE_EXEMPT.
RUN_SOURCES: dict[str, RunSource] = {
    source.feature: source
    for source in (
        IOC_LOOKUP_RUN_SOURCE,
        USERNAME_SEARCH_RUN_SOURCE,
        EMAIL_SEARCH_RUN_SOURCE,
        REDDIT_SEARCH_RUN_SOURCE,
    )
}

_NOT_YET = "not in investigations v1 - needs its report sections and entity extractor"

RUN_SOURCE_EXEMPT: dict[str, str] = {
    "phone_search": _NOT_YET,
    "git_recon": _NOT_YET,
    "ru_business_check": _NOT_YET,
    "amass": _NOT_YET,
    "steam_recon": _NOT_YET,
    "instagram_search": _NOT_YET,
    "telegram_search": _NOT_YET,
}


def get_run_source(feature: str) -> RunSource | None:
    return RUN_SOURCES.get(feature)
