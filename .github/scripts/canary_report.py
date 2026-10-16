#!/usr/bin/env python3
"""Summarize a source-canary JUnit report (`.github/workflows/canary.yml`). Stdlib only.

Usage: canary_report.py REPORT.xml [--issue-body PATH]

- Writes a passed/failed/skipped table plus the failed tests and every skip reason to
  `$GITHUB_STEP_SUMMARY` (stdout when unset) - skip reasons matter: a source that answers the
  runner 403 for weeks is otherwise invisible.
- Writes `failed=<n>` to `$GITHUB_OUTPUT` when set, for the issue/Telegram steps.
- With `--issue-body`, writes the failed-test list and a link to this run (from GitHub's
  `GITHUB_SERVER_URL`/`GITHUB_REPOSITORY`/`GITHUB_RUN_ID`) there, when anything failed.

A missing or empty report (pytest never ran, e.g. the install step failed) counts as nothing
run, not as a failure: the job itself is already red in that case. Always exits 0 - the pytest
step's own exit code is what fails the job.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Report:
    passed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (test id, message)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (test id, reason)
    found: bool = True


def _test_id(case: ET.Element) -> str:
    classname = case.get("classname", "")
    name = case.get("name", "")
    return f"{classname}::{name}" if classname else name


def _first_line(text: str | None) -> str:
    return (text or "").strip().splitlines()[0] if (text or "").strip() else ""


def parse_report(path: Path) -> Report:
    if not path.is_file() or path.stat().st_size == 0:
        return Report(found=False)
    report = Report()
    for case in ET.parse(path).getroot().iter("testcase"):
        test_id = _test_id(case)
        problem = case.find("failure")
        if problem is None:
            problem = case.find("error")
        skipped = case.find("skipped")
        if problem is not None:
            message = problem.get("message") or _first_line(problem.text)
            report.failed.append((test_id, message))
        elif skipped is not None:
            report.skipped.append((test_id, skipped.get("message") or _first_line(skipped.text)))
        else:
            report.passed.append(test_id)
    return report


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def run_url() -> str | None:
    server, repo, run_id = (
        os.environ.get("GITHUB_SERVER_URL"),
        os.environ.get("GITHUB_REPOSITORY"),
        os.environ.get("GITHUB_RUN_ID"),
    )
    return f"{server}/{repo}/actions/runs/{run_id}" if server and repo and run_id else None


def render_summary(report: Report) -> str:
    if not report.found:
        return "## Source canaries\n\nNo JUnit report - the canaries did not run.\n"
    lines = [
        "## Source canaries",
        "",
        "| Passed | Failed | Skipped |",
        "| ---: | ---: | ---: |",
        f"| {len(report.passed)} | {len(report.failed)} | {len(report.skipped)} |",
        "",
    ]
    if report.failed:
        lines += ["### Failed", "", "| Test | Message |", "| --- | --- |"]
        lines += [f"| `{t}` | {_cell(m)} |" for t, m in report.failed]
        lines.append("")
    if report.skipped:
        lines += ["### Skipped", "", "| Test | Reason |", "| --- | --- |"]
        lines += [f"| `{t}` | {_cell(r)} |" for t, r in report.skipped]
        lines.append("")
    return "\n".join(lines)


def render_issue_body(report: Report, url: str | None) -> str:
    lines = [f"{len(report.failed)} source canary test(s) failed:", ""]
    lines += [f"- `{t}`: {m}" if m else f"- `{t}`" for t, m in report.failed]
    if url:
        lines += ["", f"Run: {url}"]
    return "\n".join(lines) + "\n"


def _append(env_var: str, text: str) -> bool:
    target = os.environ.get(env_var)
    if not target:
        return False
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(text)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report", type=Path)
    parser.add_argument("--issue-body", type=Path)
    args = parser.parse_args(argv)

    report = parse_report(args.report)
    summary = render_summary(report)
    if not _append("GITHUB_STEP_SUMMARY", summary):
        sys.stdout.write(summary)
    _append("GITHUB_OUTPUT", f"failed={len(report.failed)}\n")
    if args.issue_body and report.failed:
        args.issue_body.write_text(render_issue_body(report, run_url()), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
