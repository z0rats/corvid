# Fuzzing

Coverage-guided fuzz harnesses using [Atheris](https://github.com/google/atheris)
(libFuzzer for Python). Not wired into CI and not part of `requirements.txt`/the
production image — install and run manually when touching parsing code that
handles untrusted input.

```bash
uv pip install atheris   # Linux x86_64 only; no macOS or arm64 wheels
python fuzz/fuzz_ioc_type.py -max_total_time=60
```

A crash is written to `crash-<hash>` in the working directory; rerun the harness
with that file as an argument to reproduce it deterministically.

## Harnesses

- `fuzz_ioc_type.py` — `determine_ioc_type`/`normalize_address`
  (`ioc_tools/ioc_lookup`). Both are pure regex classifiers run on every value
  pasted into the command palette, IOC lookup, and newsfeed IOC extraction with
  no prior validation; some patterns (URL/DOMAIN) use nested quantifiers, the
  classic shape for catastrophic backtracking (ReDoS) — libFuzzer's own
  `-timeout` flag catches that class of bug by reporting a pathologically slow
  input as a crash.

Add a new harness here for any other pure, input-parsing function reachable
from untrusted data (e.g. header/IOC parsing in `email_analyzer`).
