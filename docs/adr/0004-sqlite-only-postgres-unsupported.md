# SQLite is the only supported backend; PostgreSQL is untested

`database.py`'s `_to_async_url` converts a `postgresql://` URL to `asyncpg`, so Postgres is technically reachable through the same SQLAlchemy models. But no test in the suite runs against it, CI never starts a Postgres container, and no doc lists it as a deployment option.

Corvid targets a self-hosted, single operator, and a SQLite file is the simplest possible path to that (`docker compose up`, zero external services). SQLAlchemy makes a second dialect nearly free at the code level, so the Postgres path was left in as a placeholder for a possible future multi-user mode rather than removed — but it's not exercised anywhere, so it should be treated as unsupported: a "doesn't work on Postgres" report is low priority until there's a separate decision to make Postgres an officially supported backend, with the test coverage that implies.
