from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config.settings import settings


def _build_security_headers() -> list[tuple[bytes, bytes]]:
    """Build security headers based on the current environment.

    CSP is only applied in production because Swagger UI requires inline scripts
    that would be blocked by a strict script-src policy in development.
    HSTS is production-only since it must not be sent over plain HTTP.
    """
    headers: list[tuple[bytes, bytes]] = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"x-permitted-cross-domain-policies", b"none"),
    ]
    if settings.environment == "production":
        headers.extend([
            (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
            (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"),
        ])
    return headers


class SecurityHeadersMiddleware:
    """Pure ASGI middleware that adds security headers to all HTTP responses"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._headers = _build_security_headers()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        is_static = path.startswith("/static/") or path.startswith("/feedicons/")

        async def send_with_security_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self._headers)
                if not is_static:
                    headers.extend([
                        (b"cache-control", b"no-store, max-age=0"),
                        (b"pragma", b"no-cache"),
                    ])
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
