"""username_search runs as investigation items: report sections and graph entities."""

from typing import Any

from app.core.entities.model import Extraction, entity
from app.core.reports.schemas import ReportRow, ReportSection
from app.core.run_sources.source import RunSource
from app.features.username_search.crud.username_search_crud import USERNAME_SEARCH_SCANS
from app.features.username_search.models.username_search_models import MaigretSearch

_SOURCE_LABELS = {
    "maigret": "Maigret",
    "social_analyzer": "social-analyzer",
    "threat_actor_usernames": "Threat actor usernames",
}


def build_sections(search: MaigretSearch, locale: str) -> list[ReportSection]:
    summary = ReportSection(
        title="Username search",
        rows=[
            ReportRow("Username", search.username),
            ReportRow("Source", _SOURCE_LABELS.get(search.source, search.source)),
            ReportRow("Status", search.status),
            ReportRow("Started at", search.started_at.strftime("%Y-%m-%d %H:%M UTC")),
            ReportRow("Sites checked", str(search.total_sites_checked)),
            ReportRow("Found", str(search.found_count)),
        ],
    )
    if search.error_message:
        summary.rows.append(ReportRow("Error", search.error_message))
    found = ReportSection(
        title="Found accounts",
        rows=[
            ReportRow(result.site_name, result.url_user, href=result.url_user)
            for result in search.site_results
        ],
    )
    return [summary, found] if found.rows else [summary]


def extract_entities(search: MaigretSearch) -> Extraction:
    root = entity("username", search.username)
    out = Extraction(root=root)
    for result in search.site_results:
        if not result.url_user:
            continue
        account = entity("account", result.url_user, f"{result.site_name}: {search.username}")
        out.link(root, account, "account")
    return out


def _target(search: Any) -> str:
    return search.username


USERNAME_SEARCH_RUN_SOURCE = RunSource(
    feature=USERNAME_SEARCH_SCANS.name,
    label="Username search",
    model=MaigretSearch,
    load=USERNAME_SEARCH_SCANS.history.get_with_results,
    target=_target,
    build_sections=build_sections,
    extract=extract_entities,
)
