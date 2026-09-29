# amass's collection engine runs as a background subprocess in the backend container, not a separate sidecar

amass v5 (unlike v3/v4, and unlike every other Go CLI this app shells out to - subfinder,
httpx) split into a client/server architecture: `amass enum`/`amass subs` are HTTP clients
to a separate `amass engine` process that owns the actual asset graph. There is no
single-shot "run a command, read its output" invocation anymore - the engine has to be
running somewhere before a scan can happen at all. Pinning to an old v3/v4 tag (last
released 2023) instead, to keep the simple standalone-CLI shape, was considered and
rejected: shipping a two-plus-year-stale, unmaintained build of a security tool trades one
problem for a worse one.

The engine's own storage need not be Postgres - confirmed in `engine/sessions/session.go`,
it falls back to a local SQLite file (`asset.db`) under its config directory when no
database is configured. This is what makes running it inside this app's existing
deployment shape viable at all: no new required infrastructure (Postgres, a message queue),
no new `docker-compose.yaml` service.

Two ways to host the engine process were considered:

1. **A separate docker-compose sidecar** (`amass-engine` service, its own container). Cleaner
   process isolation and matches how amass's own documentation/examples run it, but adds a
   new service to every deployment of this app - more to document in the README, more moving
   parts for a self-hosted single-user tool, and a new inter-container network dependency
   (`amass_service.py` would need `AMASS_ENGINE_URL` pointed at the sidecar's hostname rather
   than `127.0.0.1`).
2. **A background subprocess inside the existing backend container**, started once at app
   startup (`main.py`'s `handle_application_startup`, alongside `start_bot_polling()`) and
   left running for the process's life.

Chosen: (2). It fits this app's existing precedent for a persistent background process
(`telegram_bot/service/polling_service.py`, see `docs/adr/0012-telegram-bot-polling.md`) and
keeps the amass feature's operational footprint at zero new deployment surface - an operator
running `docker compose up` gets it for free, the same way they get the scheduler and the
Telegram poll loop. The tradeoff is that the engine's lifecycle is now coupled to the backend
process's own lifecycle (a backend restart also restarts the engine, briefly interrupting any
in-flight `enum` call), and the two processes share the container's resource limits rather
than having independent ones - both accepted as reasonable for a single-user, "not
production-hardened" app (per the project's own framing) where a sidecar's operational
cleanliness isn't worth the added deployment complexity.

`amass_engine_service.py`'s `ensure_engine_ready()` is called defensively before every scan
(not just relied on the startup task) - it's idempotent (a lock guards against a concurrent
caller spawning a second engine process) and self-healing if the engine process ever dies
between scans, without needing a supervisor process of its own.

amass's own `-timeout` flag on `enum` is an *idle* timeout (minutes without new discoveries),
not a wall-clock cap, so `amass_service.py` layers its own hard `WALL_CLOCK_TIMEOUT_SECONDS`
ceiling via `asyncio.wait_for` + `ProcessCancellable` - a domain with a steady trickle of new
findings could otherwise run indefinitely. Hitting that ceiling is treated as the scan being
`cancelled`, not `failed`: the engine's asset store already has whatever it found, and
`amass subs` reads it back regardless of how `enum` ended (finished naturally, hit the
ceiling, or was cancelled by the user) - `cancelled` communicates "stopped before finishing
naturally, here's what's known so far" more honestly than `failed` would for what is, for
this tool, an expected outcome rather than an error.
