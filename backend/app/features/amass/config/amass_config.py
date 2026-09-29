# Tunables for the amass feature (owasp-amass v5 integration). Hardcoded rather
# than a persisted settings module - like git_recon/reddit_search, nothing here
# is meaningfully worth letting the analyst tune per-deployment.

BINARY_NAME = "amass"
READY_CHECK_BINARY = "ae_isready"
ENGINE_HOST = "127.0.0.1"

# amass's own `enum -timeout` is an *idle* timeout (minutes without new
# discoveries before it stops on its own), not a hard ceiling - a domain with
# a steady trickle of new findings can run indefinitely. This is a genuine
# hard wall-clock cap on the enum subprocess, independent of that flag,
# mirroring social_analyzer_config.py's PROCESS_WATCHDOG_SECONDS.
WALL_CLOCK_TIMEOUT_SECONDS = 600
ENUM_IDLE_TIMEOUT_MINUTES = 3

# How long to poll ae_isready for after starting the engine subprocess, and the
# gap between polls.
ENGINE_READY_TIMEOUT_SECONDS = 30
ENGINE_READY_POLL_SECONDS = 1

# `amass subs` only reads back from the engine's local SQLite store - should
# always be fast, generous ceiling just as a backstop against a wedged process.
SUBS_TIMEOUT_SECONDS = 30
