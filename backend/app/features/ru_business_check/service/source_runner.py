"""One interface for every source a scan queries after ЕГРЮЛ.

Each source (live registry, ГИР БО/МСП, local dump) is a `Source`: which subject it needs,
how to fetch, what it records when it didn't run, and where the result is stored.
`run_source` turns it into a `SourceResult` whose `status` is the one place that decides
whether a source counts as checked (docs/adr/0014-*.md: a failure is "not checked", never an
empty result). A source failing for *any* network/parse reason - its own error class, an
`httpx` transport/status error, a malformed JSON body - is a failed source, not a failed
scan.
"""

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

import httpx

logger = logging.getLogger(__name__)

# checked        - ran and read everything the verdict relies on
# incomplete     - ran, but part of what it covers wasn't read (kept, but not "checked")
# failed         - raised; recorded as its `empty` result
# skipped        - its subject (ИНН / director) is unknown for this entity
# not_applicable - can't apply to this entity type (e.g. the ЦБ list for an ИП)
SourceStatus = Literal["checked", "incomplete", "failed", "skipped", "not_applicable"]


@dataclass(frozen=True)
class SourceContext:
    """What ЕГРЮЛ resolved - the only inputs a source gets."""

    inn: str | None
    director: str | None
    is_individual: bool


@dataclass(frozen=True)
class Source:
    """`fetch(subject, ctx) -> (data, raw)` - `subject` is the ИНН or director (`needs`),
    never empty - with `raw=None` for a source with no remote payload (a local
    dump). `data_column`/`raw_column` name the dedicated search-row columns; `None` stores
    the result under `extra_data[key]`/`extra_raw[key]` instead (ADR 0014 §3). `empty` is
    what a dedicated source records when it didn't run - an extra source records nothing."""

    key: str
    fetch: Callable[[str, SourceContext], Awaitable[tuple[Any, str | None]]]
    error: type[Exception]
    needs: Literal["inn", "director"] = "inn"
    data_column: str | None = None
    raw_column: str | None = None
    empty: Callable[[], Any] | None = None
    is_complete: Callable[[Any, SourceContext], bool] | None = None
    not_applicable_to_individual: Callable[[], dict] | None = None


@dataclass(frozen=True)
class SourceResult:
    key: str
    status: SourceStatus
    data: Any
    raw: str | None

    @property
    def checked(self) -> bool:
        return self.status == "checked"


def _not_run(source: Source, status: SourceStatus) -> SourceResult:
    empty = source.empty() if source.empty else None
    return SourceResult(source.key, status, empty, "" if source.empty else None)


async def run_source(source: Source, ctx: SourceContext) -> SourceResult:
    subject = ctx.director if source.needs == "director" else ctx.inn
    if not subject:
        return _not_run(source, "skipped")
    if ctx.is_individual and source.not_applicable_to_individual is not None:
        return SourceResult(
            source.key, "not_applicable", source.not_applicable_to_individual(), None
        )
    try:
        data, raw = await source.fetch(subject, ctx)
    except (source.error, httpx.HTTPError, json.JSONDecodeError) as exc:
        logger.warning("ru_business_check: %s lookup failed for %r: %s", source.key, subject, exc)
        return _not_run(source, "failed")
    if source.is_complete is not None and not source.is_complete(data, ctx):
        return SourceResult(source.key, "incomplete", data, raw)
    return SourceResult(source.key, "checked", data, raw)


def empty_fields(sources: list[Source]) -> dict[str, Any]:
    """Every dedicated column's "not checked" value plus empty extra/digest maps - what a
    search row carries before (or without) any source running."""
    fields: dict[str, Any] = {}
    for source in sources:
        if source.data_column:
            fields[source.data_column] = source.empty() if source.empty else None
            if source.raw_column:
                fields[source.raw_column] = ""
    return {**fields, "extra_data": {}, "extra_raw": {}, "raw_sha256": {}}


def store_results(sources: list[Source], results: list[SourceResult]) -> dict[str, Any]:
    """`results` -> the search-row fields they occupy (dedicated columns or `extra_*`)."""
    by_key = {s.key: s for s in sources}
    fields = empty_fields(sources)
    for result in results:
        source = by_key[result.key]
        if source.data_column:
            fields[source.data_column] = result.data
            if source.raw_column:
                fields[source.raw_column] = result.raw or ""
        elif result.data is not None:
            fields["extra_data"][result.key] = result.data
            if result.raw is not None:
                fields["extra_raw"][result.key] = result.raw
    return fields
