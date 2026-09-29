"""Regression guard: Instaloader's file-based session methods
(`load_session_from_file`/`save_session_to_file`, on both `Instaloader` and
`InstaloaderContext`) serialize through `pickle` - loading a session from
untrusted/user-supplied file content via them is arbitrary code execution.
This feature only ever uses the dict-based API (`load_session`/`save_session`),
per docs/architecture/instagram-search.md. This walks every backend source file
and fails if either banned method name appears anywhere in `app/`, so a future
change can't reintroduce the file-based path.
"""

import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"

_BANNED_METHOD_RE = re.compile(r"\b(load_session_from_file|save_session_to_file)\b")


def test_no_pickle_based_session_methods_in_app():
    offenders = []
    for path in APP_ROOT.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        if _BANNED_METHOD_RE.search(content):
            offenders.append(path.relative_to(APP_ROOT).as_posix())

    assert not offenders, (
        "File(s) reference Instaloader's pickle-based session methods "
        f"(load_session_from_file/save_session_to_file): {offenders}. Use the dict-based "
        "load_session(username, sessiondata)/save_session() API instead - see "
        "docs/architecture/instagram-search.md."
    )
