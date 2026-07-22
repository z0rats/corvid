# Security Policy

Corvid is a single-user, self-hosted tool aimed at security analysts, so it's reasonable to
expect it to hold itself to a decent security bar. This document explains how to report a
problem, and keeps a record of the notable issues that have already been found and fixed.

## Supported Versions

Corvid doesn't maintain long-term release branches — only the latest commit on `main` receives
security fixes. If you're running an older checkout, update before reporting an issue you
haven't reproduced against current `main`.

## Reporting a Vulnerability

Please **don't open a public GitHub issue** for anything that looks exploitable.

Instead, report it privately:

- Preferred: [GitHub Security Advisories](https://github.com/z0rats/corvid/security/advisories/new)
  for this repository.
- Alternative: email **z0rats.alex@gmail.com** with a description of the issue, steps to
  reproduce, and its potential impact.

This is a solo-maintained project, so response times aren't guaranteed, but reports are taken
seriously and triaged as they come in. If a fix is warranted, credit is given in the fix's commit
message and, for anything significant, in the section below — unless you'd rather stay anonymous.

## Scope

Things worth reporting: authentication/authorization bypass, SSRF (this app fetches
attacker-influenceable URLs server-side in several places — see `ssrf_guard.py`), secret/API-key
disclosure, injection (SQL, template, command), path traversal, and anything that lets one
Corvid instance be used to attack infrastructure the operator doesn't control.

Generally out of scope: issues that only reproduce with
`SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS=true` (an explicit, documented opt-out meant for
dev/testing only), vulnerabilities in the third-party OSINT libraries Corvid shells out to or
vendors (`maigret`, `social-analyzer`, `mailcat-osint`, etc. — please report those upstream),
and denial-of-service reports against a tool that's meant to run on infrastructure you already
control.

## Past Vulnerabilities

Corvid started as a fork with no dedicated security review, so a pass was done to find and close
the gaps below. None of these had a public advisory filed (they were caught internally rather
than reported), but they're recorded here for transparency since they affected real deployments.

### No authentication on the API (fixed)

Every `/api/*` route, plus `/docs` and `/openapi.json`, was reachable by anyone who could reach
the container's port — there was no login and no token check anywhere in the request path. On a
tool that stores third-party API keys and investigation history, that's a straight path to
reading or triggering lookups on someone else's behalf. Fixed by gating every router behind a
single shared bearer token (`core/security/access_control.py`), generated on first run and
required on every request thereafter; only the health check and the WebSocket handshake (which
authenticates itself separately, since browsers can't set a custom header during a WS upgrade)
are exempt.

### API keys stored in plaintext (fixed)

Third-party provider keys (VirusTotal, Shodan, etc.) were written to the database exactly as
entered. Anyone with read access to the SQLite file — a backup, a misconfigured volume mount,
another process on the host — got every configured key for free. Fixed with transparent
Fernet encryption at the SQLAlchemy column level (`EncryptedString` in
`api_keys_settings_models.py`); the encryption key itself is generated once and persisted with
restrictive file permissions, separate from the database.

### SSRF guard didn't cover redirects (fixed)

The original guard resolved and validated a URL's hostname once, up front, then handed the
*original* URL to `httpx` with redirect-following left on. Two gaps followed from that: a
malicious server could return a `3xx` pointing at an internal address and the client would
happily follow it without re-checking, and even the initial request wasn't pinned to the IP that
was actually validated, leaving a window for DNS rebinding between the check and the connect.
Fixed by pinning every request to its validated IP and manually walking redirects
one hop at a time, re-validating the target on each hop instead of trusting `httpx`'s built-in
redirect handling.

### API keys leaking into application logs (fixed)

Several lookup providers (Hunter.io, Pulsedive, Shodan, Google Safe Browsing, IPQualityScore)
put their API key directly in the request URL rather than a header. A broad
`except Exception: logger.error(..., str(e))` around any of those calls would render the full
URL — key included — straight into `data/logs/*.log`. Fixed with a logging filter
(`log_redaction.py`) that pattern-matches and scrubs key-shaped substrings out of every log
record before it's written, regardless of which provider or code path produced it.

### API docs reachable without credentials (fixed)

Swagger UI and the raw OpenAPI schema were only ever gated by `ENVIRONMENT != "production"`,
not by anything resembling a credential — in any non-production deployment (including one
exposed by mistake) they were open to whoever found the URL, handing over the full internal
route map. Fixed by disabling FastAPI's built-in docs routes unconditionally and re-registering
equivalents that sit behind the same access-token dependency as everything else.

### Container ran as root (fixed)

The backend image had no `USER` directive, so the app process — including code that parses
untrusted file uploads (`.eml` files) and shells out to third-party OSINT CLIs — ran as root
inside its container. Fixed by adding a dedicated non-root user; the entrypoint briefly starts
as root only long enough to fix ownership of the bind-mounted data directory, then drops
privileges before `exec`-ing into `uvicorn`.

### WebSocket alerts channel authenticated only if explicitly configured (fixed)

The alerts WebSocket checked an optional `API_WS_SECRET_TOKEN` that defaulted to empty, meaning
auth was silently disabled unless an operator went out of their way to set it — an easy default
to miss, and inconsistent with the rest of the API. Fixed by requiring the same mandatory access
token as every other route, checked via the same comparison path.
