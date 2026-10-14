"""Browser-usable /docs (Swagger UI) and /redoc pages for the token-gated API.

A browser following a link can't attach the `Authorization: Bearer` header every API route
requires, so the stock FastAPI pages behind the token just 401. Instead the two HTML shells are
public - they carry no data, only a loader - while `/openapi.json` (the actual API description)
stays behind the token. Each shell's inline script reads the token the SPA already stored in
localStorage (same origin behind the bundled nginx) and sends it: Swagger UI on every request it
makes (so "Try it out" works too), ReDoc on its one spec fetch.

Not mounted in production, same as before (see `add_docs_routes`).
"""

import html

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse

from app.core.config.settings import settings
from app.core.security.access_control import verify_access_token

# Must match the SPA's key (frontend/src/core/utils/accessToken.js); a test keeps them in sync.
TOKEN_STORAGE_KEY = "corvid_access_token"

_SWAGGER_JS = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
_SWAGGER_CSS = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
_REDOC_JS = "https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"

_NO_TOKEN_MESSAGE = (
    "Sign in to Corvid in this browser first (open the app and enter the access token), "
    "then reload this page."
)


def _page(title: str, head: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
{head}
</head>
<body>
<p id="no-token" hidden style="font-family: sans-serif; margin: 1rem">{_NO_TOKEN_MESSAGE}</p>
{body}
</body>
</html>
"""
    )


_READ_TOKEN_JS = f"""
const token = localStorage.getItem("{TOKEN_STORAGE_KEY}") || "";
if (!token) document.getElementById("no-token").hidden = false;
"""


def swagger_ui_page(title: str) -> HTMLResponse:
    return _page(
        title,
        f'<link rel="stylesheet" href="{_SWAGGER_CSS}">',
        f"""<div id="swagger-ui"></div>
<script src="{_SWAGGER_JS}"></script>
<script>
{_READ_TOKEN_JS}
SwaggerUIBundle({{
  url: "/openapi.json",
  dom_id: "#swagger-ui",
  layout: "BaseLayout",
  deepLinking: true,
  showExtensions: true,
  showCommonExtensions: true,
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
  requestInterceptor: (request) => {{
    if (token) request.headers.Authorization = "Bearer " + token;
    return request;
  }},
}});
</script>""",
    )


def redoc_page(title: str) -> HTMLResponse:
    return _page(
        title,
        "<style>body { margin: 0; padding: 0; }</style>",
        f"""<div id="redoc"></div>
<script src="{_REDOC_JS}"></script>
<script>
{_READ_TOKEN_JS}
fetch("/openapi.json", {{ headers: token ? {{ Authorization: "Bearer " + token }} : {{}} }})
  .then((response) => {{
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  }})
  .then((spec) => Redoc.init(spec, {{}}, document.getElementById("redoc")))
  .catch(() => {{ document.getElementById("no-token").hidden = false; }});
</script>""",
    )


def add_docs_routes(app: FastAPI) -> None:
    """Mount /openapi.json (token-gated) and the public /docs and /redoc shells that load it.

    fastapi_config.py disables FastAPI's own auto-registered docs routes unconditionally;
    these replacements stay off entirely in production.
    """
    if settings.environment == "production":
        return

    @app.get("/openapi.json", include_in_schema=False, dependencies=[Depends(verify_access_token)])
    async def get_openapi_json():
        return app.openapi()

    @app.get("/docs", include_in_schema=False)
    async def get_docs():
        return swagger_ui_page(f"{app.title} - Swagger UI")

    @app.get("/redoc", include_in_schema=False)
    async def get_redoc():
        return redoc_page(f"{app.title} - ReDoc")
