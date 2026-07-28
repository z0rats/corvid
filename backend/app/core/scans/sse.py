import asyncio
import json

from fastapi.responses import StreamingResponse


def sse_response(queue: asyncio.Queue) -> StreamingResponse:
    """Stream dict events off `queue` as Server-Sent Events, one `data: {json}\\n\\n`
    line per event, until a `None` sentinel is put on the queue.

    Shared by every scan-style feature (username_search, email_search, git_recon):
    each route handler starts its scan as a detached `asyncio.create_task()` and
    hands this the queue that task reports progress on, so the request can stream
    live progress for however long the scan takes rather than blocking behind a
    reverse proxy's read timeout.
    """
    async def event_stream():
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
