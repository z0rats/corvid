"""Characterizes `sse_response` (core/scans/sse.py) against the exact contract
the three scan routers relied on when this was copy-pasted inline: dict events
off a queue, formatted as `data: {json}\\n\\n`, terminated by a `None` sentinel,
with the same Cache-Control/Connection/X-Accel-Buffering headers.
"""

import asyncio
import json

from app.core.scans.sse import sse_response


async def _drain(response):
    return [chunk async for chunk in response.body_iterator]


class TestSseResponse:
    def test_headers_and_media_type(self):
        queue: asyncio.Queue = asyncio.Queue()
        queue.put_nowait(None)

        response = sse_response(queue)

        assert response.media_type == "text/event-stream"
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"
        assert response.headers["x-accel-buffering"] == "no"

    def test_events_formatted_as_sse_data_lines(self):
        queue: asyncio.Queue = asyncio.Queue()
        queue.put_nowait({"type": "started", "search_id": 1})
        queue.put_nowait({"type": "progress", "checked": 1, "total_sites": 10})
        queue.put_nowait(None)

        chunks = asyncio.run(_drain(sse_response(queue)))

        assert chunks == [
            f"data: {json.dumps({'type': 'started', 'search_id': 1})}\n\n",
            f"data: {json.dumps({'type': 'progress', 'checked': 1, 'total_sites': 10})}\n\n",
        ]

    def test_stops_at_none_sentinel_without_consuming_further(self):
        queue: asyncio.Queue = asyncio.Queue()
        queue.put_nowait({"type": "started", "search_id": 1})
        queue.put_nowait(None)
        # Never consumed - proves the generator stops at the sentinel rather
        # than draining the whole queue.
        queue.put_nowait({"type": "progress", "checked": 1})

        chunks = asyncio.run(_drain(sse_response(queue)))

        assert len(chunks) == 1
        assert queue.qsize() == 1

    def test_waits_for_events_pushed_after_the_stream_starts(self):
        queue: asyncio.Queue = asyncio.Queue()

        async def _scenario():
            response = sse_response(queue)
            gen = response.body_iterator

            async def _produce():
                await asyncio.sleep(0.01)
                await queue.put({"type": "started", "search_id": 1})
                await queue.put(None)

            asyncio.create_task(_produce())
            return [chunk async for chunk in gen]

        chunks = asyncio.run(_scenario())
        assert chunks == [f"data: {json.dumps({'type': 'started', 'search_id': 1})}\n\n"]

    def test_returns_a_fresh_generator_per_call_no_shared_state(self):
        queue_a: asyncio.Queue = asyncio.Queue()
        queue_a.put_nowait({"type": "a"})
        queue_a.put_nowait(None)

        queue_b: asyncio.Queue = asyncio.Queue()
        queue_b.put_nowait({"type": "b"})
        queue_b.put_nowait(None)

        chunks_a = asyncio.run(_drain(sse_response(queue_a)))
        chunks_b = asyncio.run(_drain(sse_response(queue_b)))

        assert chunks_a == [f"data: {json.dumps({'type': 'a'})}\n\n"]
        assert chunks_b == [f"data: {json.dumps({'type': 'b'})}\n\n"]
