#!/usr/bin/env python3
"""Fail on mypy errors that aren't in the checked-in baseline (backend/mypy-baseline.txt).

The backend carries a pre-existing mypy backlog, so a plain blocking `mypy app` would fail every
build. This blocks only *new* errors: each one is keyed by file + message + error code (line
numbers are dropped, since unrelated edits shift them) and compared as a multiset against the
baseline. Errors fixed since the baseline was written only print a reminder to shrink it.

    python scripts/check_mypy_baseline.py            # check (CI, make lint-backend)
    python scripts/check_mypy_baseline.py --update   # rewrite the baseline to the current errors

Run with the backend venv's Python (mypy must be importable); it runs `mypy app` in backend/.
"""

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
BASELINE = BACKEND_DIR / "mypy-baseline.txt"

_ERROR_LINE = re.compile(r"^(?P<path>[^:\s]+\.py):\d+(?::\d+)?: error: (?P<rest>.*)$")
_LINE_REF = re.compile(r"\bline \d+\b")


def _run_mypy() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "app"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


def _keys(output: str) -> Counter[str]:
    keys: Counter[str] = Counter()
    for line in output.splitlines():
        match = _ERROR_LINE.match(line.strip())
        if match:
            rest = _LINE_REF.sub("line N", match["rest"].strip())
            keys[f"{match['path']}: {rest}"] += 1
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update", action="store_true", help="rewrite the baseline")
    args = parser.parse_args()

    returncode, output = _run_mypy()
    # mypy exits 1 when it found errors and 2 when it couldn't run at all (bad config, crash).
    if returncode not in (0, 1):
        print(output, file=sys.stderr)
        print(f"mypy failed to run (exit {returncode})", file=sys.stderr)
        return returncode

    current = _keys(output)
    if args.update:
        BASELINE.write_text("".join(f"{key}\n" for key in sorted(current.elements())))
        print(
            f"Wrote {sum(current.values())} error(s) to {BASELINE.relative_to(BACKEND_DIR.parent)}"
        )
        return 0

    baseline = Counter(BASELINE.read_text().splitlines()) if BASELINE.exists() else Counter()
    new = current - baseline
    fixed = baseline - current

    if fixed:
        print(
            f"{sum(fixed.values())} baseline mypy error(s) no longer occur - run "
            "`python scripts/check_mypy_baseline.py --update` to shrink the baseline."
        )
    if new:
        print(f"{sum(new.values())} new mypy error(s) not in the baseline:", file=sys.stderr)
        for line in output.splitlines():
            match = _ERROR_LINE.match(line.strip())
            if match:
                key = f"{match['path']}: {_LINE_REF.sub('line N', match['rest'].strip())}"
                if new[key] > 0:
                    print(f"  {line.strip()}", file=sys.stderr)
                    new[key] -= 1
        return 1

    print(f"mypy: no new errors ({sum(current.values())} in baseline backlog)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
