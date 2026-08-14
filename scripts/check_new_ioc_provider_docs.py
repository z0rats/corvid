#!/usr/bin/env python3
"""Pre-commit hook: if a new ioc_lookup provider is added to service_registry.py, require
the website's ioc-tools.md to be staged in the same commit.

Not a full coverage check - several providers already predate this hook and aren't listed
on the website page either, and this intentionally doesn't try to backfill that. It only
fires when the provider *count* goes up between HEAD and the staged version, so it never
blocks unrelated edits to service_registry.py (renames, bugfixes, reordering) and never
requires fixing pre-existing gaps to make an unrelated commit succeed.
"""

import re
import subprocess
import sys

REGISTRY_PATH = "backend/app/features/ioc_tools/ioc_lookup/single_lookup/service/service_registry.py"
WEBSITE_DOC_PATH = "website/src/content/docs/features/ioc-tools.md"

PROVIDER_ENTRY_RE = re.compile(r'"\w+":\s*ProviderSpec\(')


def provider_count(text: str) -> int:
    return len(PROVIDER_ENTRY_RE.findall(text))


def staged_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True
    )
    return set(result.stdout.splitlines())


def read_git_blob(ref: str) -> str | None:
    result = subprocess.run(["git", "show", ref], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def main() -> int:
    staged = staged_files()
    if REGISTRY_PATH not in staged:
        return 0

    old_content = read_git_blob(f"HEAD:{REGISTRY_PATH}")
    old_count = provider_count(old_content) if old_content is not None else 0

    new_content = read_git_blob(f":{REGISTRY_PATH}")
    if new_content is None:
        return 0
    new_count = provider_count(new_content)

    if new_count <= old_count:
        return 0

    if WEBSITE_DOC_PATH in staged:
        return 0

    print(
        f"service_registry.py gained a new provider ({old_count} -> {new_count}) but "
        f"{WEBSITE_DOC_PATH} is not staged.\n"
        "Add/update it in the same commit (or `git add` it if you already edited it), "
        "or amend this hook's intent if this provider genuinely doesn't belong there.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
