""".github/scripts/canary_report.py turns the canary workflow's JUnit report into the step
summary (with skip reasons), the `failed` count the issue step keys on, and the issue body."""

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "canary_report", Path(__file__).resolve().parents[3] / ".github/scripts/canary_report.py"
)
script = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(script)

_MIXED = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="5" failures="1" errors="1" skipped="1">
  <testcase classname="tests.canary.test_a" name="test_ok" time="0.1"/>
  <testcase classname="tests.canary.test_a" name="test_drift" time="0.2">
    <failure message="AssertionError: items lost `id`">long traceback</failure>
  </testcase>
  <testcase classname="tests.canary.test_b" name="test_broken_fixture" time="0.0">
    <error message="failed on setup with &quot;KeyError&quot;">trace</error>
  </testcase>
  <testcase classname="tests.canary.test_b" name="test_blocked[x]" time="0.0">
    <skipped type="pytest.skip" message="source not answering us: HTTP 403 | geo">skip</skipped>
  </testcase>
  <testcase classname="tests.canary.test_b" name="test_ok_too" time="0.1"/>
</testsuite></testsuites>
"""

_EMPTY = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="0" failures="0" errors="0" skipped="0"/></testsuites>
"""


def _write(tmp_path, text, name="report.xml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _clear_github_env(monkeypatch):
    for var in (
        "GITHUB_STEP_SUMMARY",
        "GITHUB_OUTPUT",
        "GITHUB_SERVER_URL",
        "GITHUB_REPOSITORY",
        "GITHUB_RUN_ID",
    ):
        monkeypatch.delenv(var, raising=False)


def test_counts_passed_failed_and_skipped_with_errors_as_failures(tmp_path):
    report = script.parse_report(_write(tmp_path, _MIXED))

    assert report.passed == ["tests.canary.test_a::test_ok", "tests.canary.test_b::test_ok_too"]
    assert report.failed == [
        ("tests.canary.test_a::test_drift", "AssertionError: items lost `id`"),
        ("tests.canary.test_b::test_broken_fixture", 'failed on setup with "KeyError"'),
    ]
    assert report.skipped == [
        ("tests.canary.test_b::test_blocked[x]", "source not answering us: HTTP 403 | geo")
    ]


def test_summary_lists_counts_failures_and_skip_reasons(tmp_path):
    summary = script.render_summary(script.parse_report(_write(tmp_path, _MIXED)))

    assert "| 2 | 2 | 1 |" in summary
    assert "`tests.canary.test_a::test_drift`" in summary
    # Skip reasons are shown, with table pipes escaped.
    assert "HTTP 403 \\| geo" in summary


def test_empty_and_missing_reports(tmp_path):
    empty = script.parse_report(_write(tmp_path, _EMPTY))
    assert empty.found and not (empty.passed or empty.failed or empty.skipped)
    assert "| 0 | 0 | 0 |" in script.render_summary(empty)

    missing = script.parse_report(tmp_path / "nope.xml")
    assert not missing.found
    assert "did not run" in script.render_summary(missing)
    assert not script.parse_report(_write(tmp_path, "", "zero.xml")).found


def test_main_writes_summary_output_and_issue_body(tmp_path, monkeypatch):
    _clear_github_env(monkeypatch)
    summary, output, body = tmp_path / "summary.md", tmp_path / "out", tmp_path / "issue.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/corvid")
    monkeypatch.setenv("GITHUB_RUN_ID", "42")

    assert script.main([str(_write(tmp_path, _MIXED)), "--issue-body", str(body)]) == 0

    assert "### Skipped" in summary.read_text()
    assert output.read_text() == "failed=2\n"
    issue = body.read_text()
    assert "2 source canary test(s) failed" in issue
    assert "- `tests.canary.test_a::test_drift`: AssertionError" in issue
    assert "Run: https://github.com/owner/corvid/actions/runs/42" in issue


def test_main_without_failures_writes_no_issue_body(tmp_path, monkeypatch, capsys):
    _clear_github_env(monkeypatch)
    body = tmp_path / "issue.md"

    assert script.main([str(_write(tmp_path, _EMPTY)), "--issue-body", str(body)]) == 0

    assert not body.exists()
    assert "## Source canaries" in capsys.readouterr().out  # no GITHUB_STEP_SUMMARY -> stdout
