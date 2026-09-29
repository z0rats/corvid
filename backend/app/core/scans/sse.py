import asyncio
import json
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse

from app.core.scans.run import OnEvent, ScanEvent


def queue_sink(queue: asyncio.Queue) -> OnEvent:
    """Adapt a `ScanRun`/`run_work` `on_event` callback onto a raw `asyncio.Queue`
    for `sse_response`: nests each `ScanEvent` as the wire's `{"type": ..., "data":
    {...}}` shape, and forwards the `None` sentinel through as-is to end the stream.
    """

    def sink(event: ScanEvent | None) -> None:
        queue.put_nowait({"type": event.type, "data": event.data} if event is not None else None)

    return sink


def sse_stream(events: AsyncIterator[dict | str]) -> StreamingResponse:
    """Stream `events` as Server-Sent Events: one `data: <json>\n\n` frame per item (a `str`
    is taken as already-serialized JSON), with the headers that keep a reverse proxy from
    buffering the stream (nginx's `X-Accel-Buffering`). The one place the wire framing lives -
    every SSE endpoint returns this, directly (an async generator) or via `sse_response`."""

    async def frames() -> AsyncIterator[str]:
        async for event in events:
            yield f"data: {event if isinstance(event, str) else json.dumps(event)}\n\n"

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def sse_response(queue: asyncio.Queue) -> StreamingResponse:
    """`sse_stream` over dict events put on `queue`, until a `None` sentinel.

    Shared by every scan-style feature: each route handler starts its scan as a detached
    `asyncio.create_task()` and hands this the queue that task reports progress on, so the
    request can stream live progress for however long the scan takes rather than blocking
    behind a reverse proxy's read timeout.
    """

    async def drain() -> AsyncIterator[dict]:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event

    return sse_stream(drain())
