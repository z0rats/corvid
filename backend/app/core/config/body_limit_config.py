import logging

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class RequestBodyLimitMiddleware:
    """ASGI middleware that rejects requests whose Content-Length exceeds a
    configurable maximum, preventing oversized payloads from consuming
    memory before they reach route handlers.

    Requests without a Content-Length header (chunked transfers) are allowed
    through — individual endpoints should enforce their own limits for
    streamed uploads.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._max_bytes = settings.api.max_request_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = _extract_content_length(scope)
        if content_length is not None and content_length > self._max_bytes:
            logger.warning(
                "Rejected request to %s: Content-Length %s exceeds limit %s",
                scope.get("path", ""),
                content_length,
                self._max_bytes,
            )
            response = JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def _extract_content_length(scope: Scope) -> int | None:
    """Extract Content-Length from request headers, returning None if absent or invalid"""
    for key, value in scope.get("headers", []):
        if key.lower() == b"content-length":
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
    return None
