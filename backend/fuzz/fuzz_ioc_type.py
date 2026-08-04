"""Atheris fuzz harness for `determine_ioc_type`/`normalize_address`.

Both are pure regex classifiers invoked on every value pasted into the command
palette, IOC lookup, and newsfeed IOC extraction - untrusted input that never
passes through any prior validation. Some of the patterns (URL/DOMAIN in
particular) use nested quantifiers, the classic shape for catastrophic
backtracking (ReDoS); libFuzzer's own `-timeout` flag turns a pathologically
slow input into a reported crash rather than just a slow pass, which is the
main class of bug worth fuzzing here since both functions are otherwise pure/
deterministic (no I/O, no shared state).

Not part of requirements.txt/the production image - install and run manually:

    uv pip install atheris
    python fuzz/fuzz_ioc_type.py -timeout=5
"""

import sys

import atheris

with atheris.instrument_imports():
    from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import (
        determine_ioc_type,
        normalize_address,
    )


def fuzz_target(data: bytes) -> None:
    text = data.decode("utf-8", errors="ignore")
    determine_ioc_type(text)
    normalize_address(text)


atheris.Setup(sys.argv, fuzz_target)
atheris.Fuzz()
