"""Resolve an investigation's items to their runs, and build its report and entity graph from
them. Each feature's part (loading, sections, entities) comes from its `RunSource`."""

import datetime
import re
from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities import graph as entity_graph
from app.core.entities.graph import Graph, RunRef
from app.core.reports.schemas import ReportRow, ReportSection
from app.core.reports.service import EXPORT_FORMATS, generate_report
from app.core.run_sources.source import RunSource
from app.features.investigations.models.investigation_models import (
    Investigation,
    InvestigationItem,
)
from app.utils.run_source_registry import get_run_source

TOP_CONNECTED_IN_REPORT = 10
_MISSING_STATUS = "Run deleted from history - results unavailable"


@dataclass
class ResolvedItem:
    item: InvestigationItem
    source: RunSource | None
    run: Any | None

    @property
    def missing(self) -> bool:
        return self.run is None


def _is_same_run(source: RunSource, item: InvestigationItem, run: Any | None) -> bool:
    """A run row with the item's id is only the item's run if its target still matches: SQLite
    reuses the highest rowid after a delete, so deleting the newest run and scanning again would
    otherwise silently point the item at an unrelated new run instead of a tombstone."""
    return run is not None and source.target(run) == item.target


async def missing_item_ids(db: AsyncSession, items: Collection[InvestigationItem]) -> set[int]:
    """Ids of the items whose run is gone (or whose feature is no longer supported) - one `id`
    query per feature, without loading any run's results. For views that only need the flag."""
    by_feature: dict[str, list[InvestigationItem]] = {}
    for item in items:
        by_feature.setdefault(item.feature, []).append(item)
    missing: set[int] = set()
    for feature, feature_items in by_feature.items():
        source = get_run_source(feature)
        if source is None:
            missing.update(item.id for item in feature_items)
            continue
        model: Any = source.model
        run_ids = {item.run_id for item in feature_items}
        # The run rows alone: every source's target is a column of it, results aren't needed.
        rows = (await db.execute(select(model).where(model.id.in_(run_ids)))).scalars()
        found = {run.id: run for run in rows}
        missing.update(
            item.id
            for item in feature_items
            if not _is_same_run(source, item, found.get(item.run_id))
        )
    return missing


async def resolve_items(db: AsyncSession, investigation: Investigation) -> list[ResolvedItem]:
    """Each item with its run and all its results, or None for a run deleted from history (or a
    feature no longer supported) - a tombstone, never an error. For the report and the graph;
    views that only need the tombstone flag use `missing_item_ids`."""
    resolved = []
    for item in investigation.items:
        source = get_run_source(item.feature)
        run = await source.load(db, item.run_id) if source else None
        if source is not None and not _is_same_run(source, item, run):
            run = None
        resolved.append(ResolvedItem(item, source, run))
    return resolved


def build_graph(resolved: list[ResolvedItem], types: Collection[str] | None = None) -> Graph:
    graph = entity_graph.merge(
        (RunRef(r.item.feature, r.item.run_id), r.source.extract(r.run))
        for r in resolved
        if r.source is not None and r.run is not None
    )
    return entity_graph.cap(entity_graph.filter_types(graph, types))


def _feature_label(resolved: ResolvedItem) -> str:
    return resolved.source.label if resolved.source else resolved.item.feature


def _fmt(value: datetime.datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC")


def build_report_sections(
    investigation: Investigation, resolved: list[ResolvedItem], locale: str
) -> list[ReportSection]:
    cover = ReportSection(
        title="Investigation",
        rows=[
            ReportRow("Name", investigation.name),
            ReportRow("Created", _fmt(investigation.created_at)),
            ReportRow("Items", str(len(resolved))),
        ],
    )
    if investigation.notes:
        cover.rows.append(ReportRow("Notes", investigation.notes))
    missing = sum(r.missing for r in resolved)
    if missing:
        cover.rows.append(ReportRow("Deleted from history", str(missing)))
    sections = [cover]

    per_feature = Counter(_feature_label(r) for r in resolved)
    if per_feature:
        sections.append(
            ReportSection(
                title="Items per feature",
                rows=[ReportRow(label, str(count)) for label, count in per_feature.most_common()],
            )
        )

    for index, r in enumerate(resolved, start=1):
        header = ReportSection(
            title=f"{index}. {_feature_label(r)}: {r.item.target}",
            rows=[ReportRow("Added", _fmt(r.item.added_at))],
        )
        if r.item.note:
            header.rows.append(ReportRow("Note", r.item.note))
        if r.missing:
            header.rows.append(ReportRow("Status", _MISSING_STATUS))
        sections.append(header)
        if r.source is not None and r.run is not None:
            for section in r.source.build_sections(r.run, locale):
                sections.append(ReportSection(title=f"{index}. {section.title}", rows=section.rows))

    top = entity_graph.top_connected(build_graph(resolved), TOP_CONNECTED_IN_REPORT)
    if top:
        sections.append(
            ReportSection(
                title="Top connected entities",
                rows=[
                    ReportRow(
                        f"{node.entity.type}: {node.entity.label}",
                        f"{node.degree} link{'s' if node.degree != 1 else ''}, "
                        f"from {len(node.sources)} run{'s' if len(node.sources) != 1 else ''}",
                    )
                    for node in top
                ],
            )
        )
    return sections


def generate_investigation_report(
    investigation: Investigation, resolved: list[ResolvedItem], fmt: str, locale: str = "en"
) -> tuple[bytes, str, str]:
    """Returns (content, media_type, filename)."""
    sections = build_report_sections(investigation, resolved, locale)
    content, media_type = generate_report(investigation.name, sections, fmt, locale)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", investigation.name).strip("_")[:80] or "report"
    filename = f"investigation-{investigation.id}-{safe_name}{EXPORT_FORMATS[fmt][1]}"
    return content, media_type, filename
