# Isolated per-tool venvs for CLI dependencies that conflict with the main backend venv

Two planned integrations - GHunt (`docs/specs/ghunt-integration-spec.md`) and bbot
(`docs/specs/bbot-integration-spec.md`, not yet built) - can't be installed into the main backend
venv: `ghunt>=2.3.2` requires `rich<14`, and `bbot==3.0.2` requires `tabulate==0.8.10`, both
conflicting with the main lock's `mitreattack-python==6.2.0` (`rich==15.0.0`, `tabulate==0.10.0`).
`docs/specs/README.md` records this as a shared prerequisite to be designed once and reused,
with the actual ADR deferred to whichever of the two ships first. GHunt is that first mover.

## Decision

Each conflicting tool gets its own throwaway venv at `/opt/tools/<name>`, built in its own
Dockerfile stage and copied into the runtime image - the same shape already used for this
project's Go binaries (subfinder/httpx/amass), just with `uv venv` + `uv pip install <pkg>==
<exact version>` instead of `go install`:

```dockerfile
FROM python:3.14-slim@... AS <name>-builder
COPY --from=uv /uv /usr/local/bin/uv
RUN uv venv /opt/tools/<name> && \
    uv pip install --python /opt/tools/<name>/bin/python <package>==<exact version>
```
then `COPY --from=<name>-builder /opt/tools/<name> /opt/tools/<name>` into the runtime stage. This
builder stage isn't always just a bare interpreter, though: if the package has a native
dependency without a prebuilt wheel for the base image's Python version (GHunt's case - Pillow,
no wheel yet for this image's Python 3.14), it needs the same build toolchain as the main
`builder` stage, and the runtime stage needs whatever shared libraries that dependency loads at
import time - both caught only by actually building and running the image, not by reading the
Dockerfile (see `docs/architecture/ghunt.md`'s "Build gotcha" section for the exact packages).

Consequences of this shape, applied consistently to every tool that uses it:

1. **Absolute path only, never `PATH`.** Services call `/opt/tools/<name>/bin/<binary>`
   directly (a constant in that feature's `config/` module). This project already hit shadowing
   once - the Go `httpx` binary had to be installed as `httpx-probe` because the Python `httpx`
   package's own console-script sits earlier on `PATH` - and an isolated venv makes that class of
   bug easy to reintroduce if a lookup goes through `PATH` instead.
2. **Version read via `core/utils/cli_tool_version.py`'s `get_cli_tool_version`**, not
   `importlib.metadata` - the package lives outside the main venv, so metadata lookups can't see
   it. "Is a newer version on PyPI" is a direct best-effort `fetch_latest_pypi_version` call with
   no persistence (`core/utils/pypi_version_check.py`) - the full `check_for_update` orchestration
   needs a `PypiVersionCheckMixin`-backed settings row, which isn't worth adding for a check that
   only matters at rebuild time anyway (an update never applies without rebuilding the image).
3. **Subprocess calls get a scrubbed environment and, if the tool reads any per-user session/
   config file from `$HOME` with no path override (GHunt's case), a private temp `HOME`** created
   with `tempfile.mkdtemp()`, populated only with what the tool needs, and removed in a `finally`
   regardless of outcome. No app secrets (DB credentials, other providers' API keys) are passed
   into the child process's environment.
4. **Dependabot doesn't see these pins.** It tracks `pip`/`npm-and-yarn`/`docker`/
   `github-actions` manifests; a version pinned inside a `RUN uv pip install <pkg>==X` line in the
   Dockerfile is invisible to it. Bumping these is a manual task - noted in AGENTS.md so it isn't
   silently forgotten the way an un-tracked pin easily can be.

## Alternatives considered

- **A single shared `/opt/tools/shared` venv for all isolated tools.** Rejected: GHunt and bbot's
  own conflicting dependency (`rich`/`tabulate`) could easily conflict with each other too, which
  would defeat the purpose immediately. One venv per tool costs a little more image size, not
  correctness risk.
- **Vendoring/patching the conflicting dependency version.** Rejected as the kind of fragile,
  update-blocking hack this project avoids elsewhere (see `docs/adr/0007-fedsfm-tls-verify-scoped-
  bypass.md` for a similar "don't paper over it" precedent) - it would need re-verifying on every
  GHunt/bbot bump instead of once at integration time.
- **A separate long-running microservice/container per tool**, the way `amass`'s v5 engine
  already works (`docs/adr/0013-amass-engine-in-container.md`). Rejected for GHunt specifically:
  amass's engine is a persistent SQLite-backed process, but GHunt is a one-shot CLI invocation per
  lookup - a whole extra container (health-checked, restarted, another network hop) is more
  operational surface than a subprocess call needs.
