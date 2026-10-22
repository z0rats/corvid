"""HTTP access to Telegram's public web pages. Fixed host: only an already-normalized channel
username reaches the path, so this sits on the SSRF guard's fixed-host allowlist."""

import httpx

from app.features.telegram_search.config.telegram_search_config import (
    DEFAULT_RETRY_AFTER_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    TME_BASE_URL,
    USER_AGENT,
)


class TelegramSourceError(Exception):
    """t.me could not be read (network error, unexpected status) - the run fails as "not
    checked", never as an empty channel."""


class TelegramRateLimitedError(TelegramSourceError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Telegram is rate-limiting requests - retry in {retry_after} s")


def _retry_after(response: httpx.Response) -> int:
    try:
        return max(1, int(response.headers.get("Retry-After", "")))
    except ValueError:
        return DEFAULT_RETRY_AFTER_SECONDS


class TmeClient:
    """`async with TmeClient() as client:` - one connection pool per scan."""

    def __init__(
        self, base_url: str = TME_BASE_URL, transport: httpx.AsyncBaseTransport | None = None
    ):
        self._base_url = base_url
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> TmeClient:
        self._client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SECONDS,
            # A redirect is a signal here (no message preview), not something to follow.
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            transport=self._transport,
        )
        return self

    async def __aexit__(self, *exc_info) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        assert self._client is not None, "TmeClient used outside `async with`"
        try:
            response = await self._client.get(f"{self._base_url}{path}", params=params)
        except httpx.HTTPError as exc:
            raise TelegramSourceError(f"Telegram is unreachable: {type(exc).__name__}") from exc
        if response.status_code == 429:
            raise TelegramRateLimitedError(_retry_after(response))
        if response.status_code >= 400:
            raise TelegramSourceError(f"Telegram answered HTTP {response.status_code}")
        return response

    async def fetch_profile_page(self, channel: str) -> str:
        """`t.me/<channel>` - answers 200 for every syntactically valid name, existing or not."""
        response = await self._get(f"/{channel}")
        if response.is_redirect:
            raise TelegramSourceError(
                f"Telegram redirected the profile page (HTTP {response.status_code})"
            )
        return response.text

    async def fetch_preview_page(self, channel: str, before: int | None = None) -> str | None:
        """One `t.me/s/<channel>` page, or None when Telegram redirects to the plain card -
        which it does for groups, users and channels with the web preview turned off."""
        response = await self._get(f"/s/{channel}", params={"before": before} if before else None)
        if response.is_redirect:
            return None
        return response.text
