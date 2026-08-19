"""Shared test infrastructure.

`async_engine`/`make_session_factory` centralize the in-memory-SQLite setup
that was previously copy-pasted (identically) across ~13 test files in
`tests/core/` and `tests/features/`. Only the table list actually varies
between callers, so that's the one thing `make_session_factory` still takes.

`patch_httpx_transport` centralizes the `httpx.MockTransport` adapter that was
copy-pasted (identically) across the tests for every scraped external source
(ru_business_check, crt.sh, the PyPI-version check) - a feature needing an
extra local patch on top (e.g. pb_nalog_service's `asyncio.sleep`) composes
its own fixture around this one instead of re-deriving the transport-swap.
"""

import asyncio

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base


def run(coro):
    """Bridge a single coroutine into a sync test function.

    NB: route all of a test's DB work through one `run()` call. The
    `async_engine` fixture below uses `StaticPool` to keep one physical
    connection alive across calls, but aiosqlite binds that connection's
    background worker thread to whichever event loop first touches it - a
    second `asyncio.run()` in the same test would hand it a *different* loop
    and silently corrupt results instead of raising.
    """
    return asyncio.run(coro)


@pytest.fixture
def async_engine():
    """A fresh in-memory SQLite engine, torn down with the test."""
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def make_session_factory(async_engine):
    """Returns a function that creates the given ORM `tables` on `async_engine`
    and hands back an `async_sessionmaker` bound to it."""

    def _make(tables):
        async def _create_tables():
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, tables=tables)

        run(_create_tables())
        return async_sessionmaker(async_engine, expire_on_commit=False)

    return _make


@pytest.fixture
def patch_httpx_transport(monkeypatch):
    """Returns a function that redirects every `httpx.AsyncClient` constructed
    for the rest of the test through `httpx.MockTransport(handler)`, so a
    provider's real request/response parsing runs against a canned response
    instead of the network."""

    def _patch(handler):
        real_async_client = httpx.AsyncClient

        def factory(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return real_async_client(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", factory)

    return _patch
