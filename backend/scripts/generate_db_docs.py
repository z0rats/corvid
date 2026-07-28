#!/usr/bin/env python3
"""Generate `docs/database-schema.md` from `Base.metadata`.

Regenerate after any model change:
    python backend/scripts/generate_db_docs.py

See docs/database-schema-audit.md section 4 (phase 4.1) for why this exists:
a hand-maintained ER diagram goes stale within a few migrations, so the only
source of truth allowed here is `Base.metadata` itself, populated by walking
`app/**/models/` the same way `migrations/env.py` does for `autogenerate`.

Tables are split into Mermaid diagrams by FK-connected component rather than
one big `erDiagram` for all of them: most tables here (singleton config rows,
`alerts`, `blacklisted_addresses`, `git_recon_searches`, ...) have zero FK
relationships, and Mermaid's default (dagre) layout has nothing to anchor
disconnected entities to - it lines them all up in one very wide row instead
of a readable grid. Splitting by connected component keeps every diagram
small; genuinely standalone tables aren't forced into a diagram at all - they
only show up in the Data Dictionary section below.

The Data Dictionary section (phase 4.2) covers every table regardless of
relationships, with the detail an ERD attribute line has no room for:
nullable and default, alongside type/key/comment.
"""
import importlib
import sys
from pathlib import Path

from sqlalchemy import CheckConstraint, TypeDecorator

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import Base  # noqa: E402

DOCS_PATH = BACKEND_DIR.parent / "docs" / "database-schema.md"

_TYPE_NAMES = {
    "Integer": "int",
    "BigInteger": "bigint",
    "SmallInteger": "smallint",
    "Text": "text",
    "Boolean": "boolean",
    "DateTime": "datetime",
    "Float": "float",
    "Numeric": "numeric",
    "JSON": "json",
}


def _import_all_models() -> None:
    """Import every model module so `Base.metadata` is fully populated.

    Mirrors `migrations/env.py::_import_all_models` for the same reason: a
    module only registers its tables on `Base.metadata` once imported, and
    nothing else this script pulls in imports all 27 model files on its own.
    """
    app_dir = BACKEND_DIR / "app"
    for models_dir in sorted(app_dir.rglob("models")):
        if not models_dir.is_dir():
            continue
        for py_file in sorted(models_dir.glob("*.py")):
            if py_file.stem == "__init__":
                continue
            module_name = ".".join(py_file.relative_to(BACKEND_DIR).with_suffix("").parts)
            importlib.import_module(module_name)


def _mermaid_type(column) -> str:
    sql_type = column.type
    if isinstance(sql_type, TypeDecorator):
        # e.g. EncryptedString stores as Text at rest - show the storage type,
        # not the Python-only wrapper class; the column's own `comment=`
        # documents encryption where it applies (see apikeys.key).
        sql_type = sql_type.impl
    type_name = type(sql_type).__name__
    if type_name == "String":
        length = getattr(sql_type, "length", None)
        return f"string({length})" if length else "string"
    return _TYPE_NAMES.get(type_name, type_name.lower())


def _sanitize(text: str) -> str:
    return " ".join(text.replace('"', "'").split())


def _column_keys(column) -> list[str]:
    keys = []
    if column.primary_key:
        keys.append("PK")
    if column.foreign_keys:
        keys.append("FK")
    if column.unique:
        keys.append("UK")
    return keys


def _column_comment(column) -> str:
    comment = _sanitize(column.comment or "")
    if not column.nullable:
        comment = f"NOT NULL. {comment}" if comment else "NOT NULL"
    return comment


def _column_default(column) -> str:
    """Client-side `default=` wins over `server_default=` for display: it's
    what SQLAlchemy actually sends on insert, which is what a reader of this
    dictionary needs when writing new code against the ORM. The one column
    with both (`maigret_searches.source`) documents identical values for
    each, so which one wins doesn't change what's shown."""
    if column.default is not None:
        arg = column.default.arg
        return "(computed)" if callable(arg) else repr(arg)
    if column.server_default is not None:
        return f"server: {column.server_default.arg}"
    return "—"


def _connected_components(tables) -> list[list[str]]:
    """Group table names by FK connectivity (undirected): a table and every
    table it references or is referenced by end up in the same component.
    Purely derived from `Base.metadata` - no hand-maintained grouping."""
    adjacency: dict[str, set[str]] = {name: set() for name in tables}
    for table_name, table in tables.items():
        for fk in table.foreign_keys:
            parent = fk.column.table.name
            adjacency[table_name].add(parent)
            adjacency[parent].add(table_name)

    seen: set[str] = set()
    components: list[list[str]] = []
    for name in sorted(tables):
        if name in seen:
            continue
        stack, component = [name], []
        seen.add(name)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda component: (-len(component), component[0]))


def _render_entity_block(table_name: str, table) -> list[str]:
    lines = [f"    {table_name} {{"]
    for column in table.columns:
        attr = f"{_mermaid_type(column)} {column.name}"
        keys = _column_keys(column)
        if keys:
            attr += f" {', '.join(keys)}"
        comment = _column_comment(column)
        if comment:
            attr += f' "{comment}"'
        lines.append(f"        {attr}")
    lines.append("    }")
    return lines


def _render_relationships(table_names: set[str], tables) -> list[str]:
    lines = []
    for table_name in sorted(table_names):
        table = tables[table_name]
        for fk in sorted(table.foreign_keys, key=lambda fk: (fk.column.table.name, fk.parent.name)):
            parent_table = fk.column.table.name
            child_cardinality = "o{" if fk.parent.nullable else "|{"
            label = f"{fk.parent.name} -> {fk.column.name}, ondelete={fk.ondelete or 'NO ACTION'}"
            lines.append(f'    {parent_table} ||--{child_cardinality} {table_name} : "{label}"')
    return lines


def _render_component_diagram(component: list[str], tables) -> str:
    lines = ["erDiagram"]
    for table_name in component:
        lines += _render_entity_block(table_name, tables[table_name])
    lines.append("")
    lines += _render_relationships(set(component), tables)
    return "\n".join(lines)


def _render_table_dictionary(table_name: str, table) -> str:
    lines = [
        f"### `{table_name}`",
        "",
        "| Column | Type | Nullable | Default | Key | Comment |",
        "|---|---|---|---|---|---|",
    ]
    for column in table.columns:
        nullable = "yes" if column.nullable else "no"
        keys = ", ".join(_column_keys(column)) or "—"
        comment = _sanitize(column.comment or "") or "—"
        lines.append(
            f"| `{column.name}` | {_mermaid_type(column)} | {nullable} | "
            f"{_column_default(column)} | {keys} | {comment} |"
        )

    checks = [c for c in table.constraints if isinstance(c, CheckConstraint) and c.name]
    if checks:
        lines.append("")
        for check in sorted(checks, key=lambda c: c.name):
            lines.append(f"- CHECK `{check.name}`: `{check.sqltext}`")
    lines.append("")
    return "\n".join(lines)


def render_markdown() -> str:
    _import_all_models()
    tables = Base.metadata.tables
    components = _connected_components(tables)
    related = [c for c in components if len(c) > 1]

    parts = [
        "<!-- AUTO-GENERATED by `python backend/scripts/generate_db_docs.py` — do not edit by hand. -->",
        "<!-- See docs/database-schema-audit.md section 4 (phases 4.1/4.2) for how this is produced. -->",
        "",
        "# Database Schema",
        "",
        "## Entity-Relationship Diagrams",
        "",
        "One diagram per group of tables connected by a foreign key. Tables with no FK "
        "relationships at all aren't shown here - Mermaid's layout has nothing to anchor "
        "disconnected entities to, so they'd end up as a wide row of boxes rather than a "
        "readable graph. Every table, related or not, is listed in the Data Dictionary below.",
        "",
    ]
    for component in related:
        parts.append(f"```mermaid\n{_render_component_diagram(component, tables)}\n```")
        parts.append("")

    parts.append("## Data Dictionary")
    parts.append("")
    parts.append(
        "Every column of every table, straight from `Base.metadata` - type, nullability, "
        "default, key (PK/FK/UK), and the `comment=` set on the model."
    )
    parts.append("")
    for table_name in sorted(tables):
        parts.append(_render_table_dictionary(table_name, tables[table_name]))

    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    content = render_markdown()
    DOCS_PATH.write_text(content)
    print(f"Wrote {DOCS_PATH.relative_to(BACKEND_DIR.parent)}")


if __name__ == "__main__":
    main()
