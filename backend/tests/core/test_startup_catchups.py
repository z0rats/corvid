"""main.py's post-startup catch-ups run sequentially in one task (SQLite has a single writer),
and one failing step doesn't stop the ones after it.

Runs in a subprocess, like test_migrations.py: importing `main` configures logging, creates
directories and builds the app against `settings` at import time, so a fresh interpreter with
DATA_DIR/LOG_DIR/DB_URL pointed at a throwaway location keeps it out of the real data/.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

SCRIPT = """
import asyncio, json
import main

events = []

def step(name, fail=False):
    async def run():
        events.append(f"start:{name}")
        await asyncio.sleep(0.01)
        if fail:
            raise RuntimeError("boom")
        events.append(f"end:{name}")
    return (name, run)

asyncio.run(main._run_startup_catchups((step("a"), step("b", fail=True), step("c"))))
print(json.dumps(events))
"""


def test_catchups_run_one_after_another_and_survive_a_failing_step(tmp_path):
    env = os.environ.copy()
    env["DB_URL"] = f"sqlite:///{tmp_path / 'test.db'}"
    env["DATA_DIR"] = str(tmp_path / "data")
    env["LOG_DIR"] = str(tmp_path / "logs")
    env["LOG_ENABLE_CONSOLE"] = "false"

    result = subprocess.run(
        [sys.executable, "-c", SCRIPT],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr
    events = json.loads(result.stdout.strip().splitlines()[-1])
    # Each step finishes (or fails) before the next starts; "c" still runs after "b" fails.
    assert events == ["start:a", "end:a", "start:b", "start:c", "end:c"]
