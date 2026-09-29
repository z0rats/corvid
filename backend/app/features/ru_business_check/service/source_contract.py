"""Shared schema-drift guard for this feature's scraped/JSON sources.

Every source client here reads a site's own undocumented response shape. Reading it with
`.get(...) or []` turns a silently renamed/removed field into an *empty* result - which
`flag_engine` and the UI then read as "checked, nothing found" (a false clean bill of
health). These helpers make a shape mismatch raise the source's own error class instead,
so `run_scan_task` records the source as not-checked (it lands in `pending_sources`, and
`flag_engine` refuses to call the verdict `low`).

`tests/features/ru_business_check/test_source_contract.py` pins every source's
parser to this behaviour structurally.
"""

from typing import Any


def _fail(error: type[ValueError], label: str, detail: str) -> ValueError:
    return error(f"{label}: схема ответа изменилась — {detail}")


def require_dict(value: Any, *, error: type[ValueError], label: str, where: str = "ответ") -> dict:
    if not isinstance(value, dict):
        raise _fail(error, label, f"{where} не JSON-объект")
    return value


def require_list_field(
    obj: Any, field: str, *, error: type[ValueError], label: str, where: str = "ответ"
) -> list:
    """`obj[field]` must exist and be a list - an empty list is a legitimate 'nothing
    found', a missing key or a non-list is drift."""
    require_dict(obj, error=error, label=label, where=where)
    value = obj.get(field)
    if not isinstance(value, list):
        raise _fail(error, label, f"нет списка «{field}» в {where}")
    return value


def require_fields(
    row: Any, fields: tuple[str, ...], *, error: type[ValueError], label: str, where: str = "запись"
) -> dict:
    """Every name in `fields` must be present as a key of `row` (its value may be None -
    a present-but-null field is data, an absent key is drift)."""
    require_dict(row, error=error, label=label, where=where)
    for field in fields:
        if field not in row:
            raise _fail(error, label, f"нет поля «{field}» в {where}")
    return row
