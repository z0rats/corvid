# SQLite is the only supported backend

Corvid targets a self-hosted, single operator, and a SQLite file is the simplest possible path to
that (`docker compose up`, zero external services).

`database.py`'s `_to_async_url` accepts only `sqlite:///` (or `sqlite+aiosqlite:///`) URLs and
raises on anything else, so a non-SQLite `DB_URL` fails at startup with a clear message. No
Postgres driver (`asyncpg`) is installed: no test ran against Postgres, CI never started a
Postgres container, and no doc offered it as a deployment option, so keeping a half-wired path
only shipped an untested driver in every image and invited "works on Postgres?" reports.
SQLAlchemy keeps a second dialect cheap to add later; doing so needs its own decision, a driver
dependency, and test coverage against a real Postgres instance.
