#!/usr/bin/env python3
"""Fail if a tracked file references a `docs/...` markdown file that doesn't exist.

Catches the failure mode where a plan/spec/audit doc is cited from code comments, ADRs and
AGENTS.md but never gets committed (or is renamed/deleted later), leaving dangling pointers.
Only `docs/<path>.md` references that start a path segment are checked, so
`website/src/content/docs/...` paths are ignored.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REF_RE = re.compile(r"(?<![\w/.-])(docs/[\w./-]+?\.md)\b")
SKIP_SUFFIXES = {".lock", ".png", ".jpg", ".svg", ".ico", ".woff2", ".pyc"}


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode()
    return [REPO_ROOT / p for p in out.split("\0") if p]


def main() -> int:
    problems: list[str] = []
    for path in tracked_files():
        if path.suffix in SKIP_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for ref in REF_RE.findall(line):
                if not (REPO_ROOT / ref).exists():
                    problems.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: missing {ref}")
    if problems:
        print("Dangling docs/ references:\n" + "\n".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
