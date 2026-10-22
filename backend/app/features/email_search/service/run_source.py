"""email_search runs as investigation items: report sections and graph entities.

A mailcat run is about a username (probed at mail providers, each hit a mailbox address); a
user_scanner run is about a full address (each hit a service it is registered at)."""

from typing import Any

from app.core.entities.model import Extraction, entity
from app.core.reports.schemas import ReportRow, ReportSection
from app.core.run_sources.source import RunSource
from app.features.email_search.crud.email_search_crud import EMAIL_SEARCH_SCANS
from app.features.email_search.models.email_search_models import MailSearch

_SOURCE_LABELS = {"mailcat": "mailcat", "user_scanner": "user_scanner"}


def build_sections(search: MailSearch, locale: str) -> list[ReportSection]:
    summary = ReportSection(
        title="Email search",
        rows=[
            ReportRow("Target", search.username),
            ReportRow("Source", _SOURCE_LABELS.get(search.source, search.source)),
            ReportRow("Status", search.status),
            ReportRow("Started at", search.started_at.strftime("%Y-%m-%d %H:%M UTC")),
            ReportRow("Providers checked", str(search.total_providers_checked)),
            ReportRow("Found", str(search.found_count)),
        ],
    )
    if search.error_count:
        summary.rows.append(ReportRow("Checks failed (not checked)", str(search.error_count)))
    if search.error_message:
        summary.rows.append(ReportRow("Error", search.error_message))
    found = ReportSection(
        title="Registered at" if search.source == "user_scanner" else "Mailboxes found",
        rows=[
            ReportRow(result.provider_name, ", ".join(result.emails or []) or "-")
            for result in search.provider_results
        ],
    )
    return [summary, found] if found.rows else [summary]


def extract_entities(search: MailSearch) -> Extraction:
    if search.source == "user_scanner":
        root = entity("email", search.username)
        out = Extraction(root=root)
        out.link_local_part(root)
        for result in search.provider_results:
            name = result.provider_name
            account = entity("account", f"{name}/{root.value}", name)
            out.link(root, account, "registered at")
        return out

    root = entity("username", search.username)
    out = Extraction(root=root)
    for result in search.provider_results:
        for address in result.emails or []:
            out.link(root, entity("email", address), "mailbox")
    return out


def _target(search: Any) -> str:
    return search.username


EMAIL_SEARCH_RUN_SOURCE = RunSource(
    feature=EMAIL_SEARCH_SCANS.name,
    label="Email search",
    model=MailSearch,
    load=EMAIL_SEARCH_SCANS.history.get_with_results,
    target=_target,
    build_sections=build_sections,
    extract=extract_entities,
)
