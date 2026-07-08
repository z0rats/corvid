from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config.settings import settings

# Swagger UI/ReDoc load their JS bundle from a CDN and run an inline init
# script, which a strict script-src would block. Both pages are already
# gated behind the access token (see access_control.py), have no user-supplied
# content to inject into, and only exist at all outside production - so they
# get a relaxed CSP instead of being excluded from it entirely.
_DOCS_PATH_PREFIXES = ("/docs", "/redoc", "/openapi.json")
_DOCS_CSP = (
    b"content-security-policy",
    b"default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    b"style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data: https://fastapi.tiangolo.com; "
    b"connect-src 'self'",
)
_APP_CSP = (
    b"content-security-policy",
    b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'",
)


def _build_base_headers() -> list[tuple[bytes, bytes]]:
    """Headers sent on every response regardless of environment or path."""
    headers: list[tuple[bytes, bytes]] = [
        (b"x-content-type-options", b"nosniff"),
        (b"x-frame-options", b"DENY"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"x-permitted-cross-domain-policies", b"none"),
    ]
    if settings.environment == "production":
        # Must not be sent over plain HTTP, which is all this app speaks by
        # default (see nginx.conf) - only meaningful behind a TLS-terminating proxy.
        headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
    return headers


class SecurityHeadersMiddleware:
    """Pure ASGI middleware that adds security headers to all HTTP responses"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._base_headers = _build_base_headers()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        is_static = path.startswith("/static/") or path.startswith("/feedicons/")
        is_docs = path.startswith(_DOCS_PATH_PREFIXES)

        async def send_with_security_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(self._base_headers)
                headers.append(_DOCS_CSP if is_docs else _APP_CSP)
                if not is_static:
                    headers.extend([
                        (b"cache-control", b"no-store, max-age=0"),
                        (b"pragma", b"no-cache"),
                    ])
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
