import asyncio

import pytest

from app.core.utils.ttl_cache import TtlCache


def test_get_fetches_once_and_caches_within_ttl():
    calls = []

    async def fetch():
        calls.append(1)
        return len(calls)

    async def go():
        cache = TtlCache(fetch, ttl_seconds=1000)
        return await cache.get(), await cache.get()

    first, second = asyncio.run(go())
    assert (first, second) == (1, 1)
    assert calls == [1]


def test_get_refetches_after_ttl_expires():
    calls = []

    async def fetch():
        calls.append(1)
        return len(calls)

    async def go():
        cache = TtlCache(fetch, ttl_seconds=0.01)
        first = await cache.get()
        await asyncio.sleep(0.02)
        second = await cache.get()
        return first, second

    assert asyncio.run(go()) == (1, 2)


def test_invalidate_forces_a_refetch_even_under_an_infinite_ttl():
    calls = []

    async def fetch():
        calls.append(1)
        return len(calls)

    async def go():
        cache = TtlCache(fetch, ttl_seconds=float("inf"))
        a = await cache.get()
        b = await cache.get()
        cache.invalidate()
        c = await cache.get()
        d = await cache.get()
        return a, b, c, d

    assert asyncio.run(go()) == (1, 1, 2, 2)


def test_concurrent_get_calls_single_flight_into_one_fetch():
    started = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def fetch():
        calls.append(1)
        started.set()
        await release.wait()
        return "value"

    async def go():
        cache = TtlCache(fetch, ttl_seconds=1000)
        first = asyncio.create_task(cache.get())
        await started.wait()
        second = asyncio.create_task(cache.get())
        await asyncio.sleep(0)
        release.set()
        return await first, await second

    assert asyncio.run(go()) == ("value", "value")
    assert calls == [1]


def test_a_failing_refetch_serves_the_last_good_value():
    async def good_fetch():
        return "good"

    async def boom():
        raise RuntimeError("upstream down")

    async def go():
        cache = TtlCache(good_fetch, ttl_seconds=0.01)
        first = await cache.get()
        cache._fetch = boom
        await asyncio.sleep(0.02)
        second = await cache.get()
        return first, second

    assert asyncio.run(go()) == ("good", "good")


def test_a_failing_first_fetch_with_no_prior_value_raises():
    async def boom():
        raise RuntimeError("upstream down")

    async def go():
        cache = TtlCache(boom, ttl_seconds=1000)
        await cache.get()

    with pytest.raises(RuntimeError, match="upstream down"):
        asyncio.run(go())
