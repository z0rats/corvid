"""Shared schema-drift guard for this feature's scraped/JSON sources.

Every source client here reads a site's own undocumented response shape. Reading it with
`.get(...) or []` turns a silently renamed/removed field into an *empty* result - which
`flag_engine` and the UI then read as "checked, nothing found" (a false clean bill of
health). These helpers make a shape mismatch raise the source's own error class instead,
so `run_scan_task` records the source as not-checked (it lands in `pending_sources`, and
`flag_engine` refuses to call the verdict `low`).

A thin Russian-language adapter over `core/external_sources/contract.py` (the shared,
language-neutral guard; `docs/adr/0022-external-source-contract.md`).
`tests/features/ru_business_check/test_source_contract.py` pins every source's
parser to this behaviour structurally.
"""

from typing import Any

from app.core.external_sources import contract

RU_MESSAGES = contract.DriftMessages(
    not_object="{label}: схема ответа изменилась — {where} не JSON-объект",
    no_list="{label}: схема ответа изменилась — нет списка «{field}» в {where}",
    no_field="{label}: схема ответа изменилась — нет поля «{field}» в {where}",
)


def require_dict(value: Any, *, error: type[ValueError], label: str, where: str = "ответ") -> dict:
    return contract.require_dict(value, error=error, label=label, where=where, messages=RU_MESSAGES)


def require_list_field(
    obj: Any, field: str, *, error: type[ValueError], label: str, where: str = "ответ"
) -> list:
    """`obj[field]` must exist and be a list - an empty list is a legitimate 'nothing
    found', a missing key or a non-list is drift."""
    return contract.require_list_field(
        obj, field, error=error, label=label, where=where, messages=RU_MESSAGES
    )


def require_fields(
    row: Any, fields: tuple[str, ...], *, error: type[ValueError], label: str, where: str = "запись"
) -> dict:
    """Every name in `fields` must be present as a key of `row` (its value may be None -
    a present-but-null field is data, an absent key is drift)."""
    return contract.require_fields(
        row, fields, error=error, label=label, where=where, messages=RU_MESSAGES
    )
