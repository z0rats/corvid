"""scripts/check_mypy_baseline.py keys errors without line numbers, so unrelated edits that
shift lines don't register as "new" errors, while a genuinely new error does."""

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_mypy_baseline", Path(__file__).resolve().parents[3] / "scripts/check_mypy_baseline.py"
)
script = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(script)


def test_keys_ignore_line_numbers_and_notes():
    before = script._keys(
        "app/a.py:10: error: Bad thing  [arg-type]\n"
        "app/a.py:11: note: some hint\n"
        'app/b.py:3:7: error: Name "x" already defined on line 2  [no-redef]\n'
        "Found 2 errors in 2 files\n"
    )
    after = script._keys(
        "app/a.py:42: error: Bad thing  [arg-type]\n"
        'app/b.py:9:1: error: Name "x" already defined on line 5  [no-redef]\n'
    )
    assert before == after
    assert sum(before.values()) == 2


def test_a_second_identical_error_counts_as_new():
    baseline = script._keys("app/a.py:1: error: Bad  [misc]\n")
    current = script._keys("app/a.py:1: error: Bad  [misc]\napp/a.py:9: error: Bad  [misc]\n")
    assert sum((current - baseline).values()) == 1
