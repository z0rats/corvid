"""When a live canary may skip rather than fail, plus the helpers every canary module runs its
live calls through. Kept apart from the canary tests so the normal suite can pin it
(`tests/canary_policy/test_policy.py`, `tests/features/ru_business_check/test_source_contract.py`).

One outcome policy for every canary, decided by `core/external_sources/outcome.py`'s `classify`:
SKIP only when the source didn't answer *us* - a network error or timeout, an
anti-bot/geo/rate-limit status (403/429/451), a server error (5xx), a captcha. Everything else
FAILS: schema drift, a JSON endpoint answering HTML, a missing field, an unexpected 404 - and a
401, since every canary source is keyless and a 401 means it now demands a key.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any, NoReturn

import httpx
import pytest

from app.core.external_sources.outcome import (
    RU_NOT_ANSWERING as UNREACHABLE,  # noqa: F401 - re-exported for the policy tests
)
from app.core.external_sources.outcome import SourceOutcome, classify


def skip_or_raise(exc: BaseException) -> NoReturn:
    """Turn a live call's exception into the canary outcome via `classify`: `pytest.skip` when
    the source didn't answer us, `pytest.fail` for a keyless source demanding a key, else
    re-raise (drift, or anything unrecognised)."""
    outcome = classify(exc)
    if outcome in (SourceOutcome.UNREACHABLE, SourceOutcome.BLOCKED):
        pytest.skip(f"source not answering us: {exc!r}")
    if outcome is SourceOutcome.AUTH:
        pytest.fail(f"keyless source now demands a key: {exc!r}")
    raise exc


def live[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run one live async call under the outcome policy."""
    try:
        return asyncio.run(coro)
    except Exception as exc:
        skip_or_raise(exc)


def get(url: str, **kwargs: Any) -> httpx.Response:
    """GET under the outcome policy; anything but a 2xx after that is a failure."""
    try:
        response = httpx.get(url, timeout=kwargs.pop("timeout", 30), **kwargs)
        response.raise_for_status()
    except Exception as exc:
        skip_or_raise(exc)
    return response


def json_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        pytest.fail(f"expected JSON, got: {response.text[:200]!r}")
