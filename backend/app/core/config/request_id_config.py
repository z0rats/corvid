import contextvars
import logging
import uuid

from starlette.types import ASGIApp, Receive, Scope, Send

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

REQUEST_ID_HEADER = "x-request-id"
MAX_REQUEST_ID_LENGTH = 128


class RequestIdMiddleware:
    """ASGI middleware that assigns a unique request ID to every HTTP request.

    If the client sends an X-Request-ID header, that value is reused
    (after length validation). Otherwise a new UUID4 is generated. The ID
    is stored in a ContextVar so that logging filters can include it
    automatically, and it is returned to the client via the X-Request-ID
    response header.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        req_id = _extract_and_validate_request_id(scope) or uuid.uuid4().hex
        request_id_ctx.set(req_id)

        async def send_with_request_id(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER.encode(), req_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)


def _extract_and_validate_request_id(scope: Scope) -> str | None:
    """Extract X-Request-ID from incoming request headers with validation.

    Rejects values that exceed MAX_REQUEST_ID_LENGTH or contain non-printable
    characters to prevent log injection and excessive memory usage.
    """
    for key, value in scope.get("headers", []):
        if key.lower() == REQUEST_ID_HEADER.encode():
            decoded = value.decode(errors="replace")
            if len(decoded) > MAX_REQUEST_ID_LENGTH:
                return None
            if not decoded.isprintable():
                return None
            return decoded
    return None


class RequestIdLogFilter(logging.Filter):
    """Logging filter that injects the current request ID into log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True
