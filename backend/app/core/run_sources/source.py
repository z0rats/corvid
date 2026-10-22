from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.model import Extraction
from app.core.reports.schemas import ReportSection


@dataclass(frozen=True)
class RunSource:
    """How cross-feature readers (investigations, their report and entity graph) treat one
    feature's stored runs, declared next to that feature's own code and registered in
    `app/utils/run_source_registry.py`.

    - `feature` is the activity-feed name (`ScanFeature.name`, or `ioc_lookup`/`reddit_search`).
    - `model` is the run's table; `id` lookups on it answer "does the run still exist" without
      loading its results.
    - `load` returns the run with whatever results the other three need, or None if it's gone.
    - `target` is what the run was about, as the activity feed shows it.
    - `build_sections` renders the run as report sections, matching the feature's own export
      where it has one.
    - `extract` is the pure run -> entities/links function for the graph.
    """

    feature: str
    label: str
    model: type
    load: Callable[[AsyncSession, int], Awaitable[Any | None]]
    target: Callable[[Any], str]
    build_sections: Callable[[Any, str], list[ReportSection]]
    extract: Callable[[Any], Extraction]
