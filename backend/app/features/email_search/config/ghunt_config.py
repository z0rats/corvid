"""Constants for the GHunt profile lookup (email -> Google account profile).

GHunt lives in its own isolated venv (`/opt/tools/ghunt`, built in `backend/Dockerfile`), not the
main backend venv - `ghunt>=2.3.2` requires `rich<14`, which conflicts with `mitreattack-python`'s
pinned `rich==15.0.0`. See docs/adr/0018-isolated-tool-cli-venvs.md for the general pattern and
docs/architecture/ghunt.md for this feature's specifics (session format, subprocess isolation,
exit-code mapping).
"""

GHUNT_BIN = "/opt/tools/ghunt/bin/ghunt"
PACKAGE_NAME = "ghunt"
SESSION_KEY_NAME = "ghunt_session"

# GHunt's own timeout is an idle/network timeout per request, not a hard wall-clock cap on the
# whole `email` subcommand - this is our own ceiling on the entire subprocess run.
TIMEOUT_SECONDS = 60

# Error codes for the frontend to localize/branch on. See docs/architecture/ghunt.md for the
# exit-code heuristic each of these maps from - GHunt has no dedicated exit code per failure
# type, so ERROR_SESSION_EXPIRED is a best-effort stderr substring match, not a guarantee.
ERROR_SESSION_MISSING = "GHUNT_SESSION_MISSING"
ERROR_SESSION_INVALID = "GHUNT_SESSION_INVALID"
ERROR_SESSION_EXPIRED = "GHUNT_SESSION_EXPIRED"
ERROR_NOT_FOUND = "GHUNT_NOT_FOUND"
ERROR_EXECUTION_ERROR = "GHUNT_EXECUTION_ERROR"
ERROR_TIMEOUT = "GHUNT_TIMEOUT"
