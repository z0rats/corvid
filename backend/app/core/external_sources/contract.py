"""Language-neutral schema-drift guard for third-party response shapes.

A source's response either matches the shape its parser reads or the parser raises a
`SourceDriftError` - never an empty result. Reading with `.get(...) or []` would turn a renamed
or removed field into "nothing found", a false clean bill of health that no caller can tell
from a genuine empty answer. A legitimately empty answer (`[]`, a header-only table) stays a
normal return value; only a shape mismatch is drift.

`classify` (`outcome.py`) maps the raised error onto `SourceOutcome.DRIFT`, so canaries and
callers treat it differently from "source unreachable". Features with their own error class and
message language (`ru_business_check`) pass `error=` and `messages=`.
"""

from dataclasses import dataclass
from typing import Any


class SourceDriftError(ValueError):
    """A source answered, but not in the shape this parser expects."""


@dataclass(frozen=True)
class DriftMessages:
    """Message templates for the three shape checks, so a feature can phrase drift in its own
    language. `{label}` is the source name, `{where}` the part of the payload, `{field}` the
    key."""

    not_object: str = "{label}: response schema changed - {where} is not a JSON object"
    no_list: str = "{label}: response schema changed - no list '{field}' in {where}"
    no_field: str = "{label}: response schema changed - no field '{field}' in {where}"


ENGLISH = DriftMessages()


def require_dict(
    value: Any,
    *,
    error: type[ValueError] = SourceDriftError,
    label: str,
    where: str = "response",
    messages: DriftMessages = ENGLISH,
) -> dict:
    if not isinstance(value, dict):
        raise error(messages.not_object.format(label=label, where=where, field=""))
    return value


def require_list_field(
    obj: Any,
    field: str,
    *,
    error: type[ValueError] = SourceDriftError,
    label: str,
    where: str = "response",
    messages: DriftMessages = ENGLISH,
) -> list:
    """`obj[field]` must exist and be a list - an empty list is a legitimate 'nothing
    found', a missing key or a non-list is drift."""
    require_dict(obj, error=error, label=label, where=where, messages=messages)
    value = obj.get(field)
    if not isinstance(value, list):
        raise error(messages.no_list.format(label=label, where=where, field=field))
    return value


def require_fields(
    row: Any,
    fields: tuple[str, ...],
    *,
    error: type[ValueError] = SourceDriftError,
    label: str,
    where: str = "record",
    messages: DriftMessages = ENGLISH,
) -> dict:
    """Every name in `fields` must be present as a key of `row` (its value may be None -
    a present-but-null field is data, an absent key is drift)."""
    require_dict(row, error=error, label=label, where=where, messages=messages)
    for field in fields:
        if field not in row:
            raise error(messages.no_field.format(label=label, where=where, field=field))
    return row
