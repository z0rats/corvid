"""A small TTL cache for a single async-fetched value: single-flight (concurrent `get()`
callers share one in-flight `fetch()`), stale-on-error (a failing refetch serves the last good
value instead of raising, once one has been loaded), and event-driven invalidation via
`invalidate()` for a caller that knows exactly when its source changed rather than only on a
wall-clock schedule."""

import logging
import time
from asyncio import Lock
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class TtlCache[T]:
    def __init__(self, fetch: Callable[[], Awaitable[T]], *, ttl_seconds: float) -> None:
        self._fetch = fetch
        self._ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._value: T | None = None
        self._has_value = False
        self._invalidated = False
        self._fetched_at = 0.0

    def invalidate(self) -> None:
        """Force the next `get()` to refetch, regardless of TTL - for a caller that can tell
        exactly when its source changed (e.g. right after its own refresh job commits) rather
        than only guessing on a wall-clock schedule."""
        self._invalidated = True

    async def get(self) -> T:
        async with self._lock:
            fresh = self._has_value and not self._invalidated
            fresh = fresh and (time.monotonic() - self._fetched_at) < self._ttl_seconds
            if fresh:
                return self._value  # type: ignore[return-value]
            try:
                value = await self._fetch()
            except Exception:
                if self._has_value:
                    logger.warning(
                        "TtlCache refresh failed; serving the last good value", exc_info=True
                    )
                    return self._value  # type: ignore[return-value]
                raise
            self._value = value
            self._has_value = True
            self._invalidated = False
            self._fetched_at = time.monotonic()
            return value
