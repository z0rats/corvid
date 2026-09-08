"""Telegram Bot API client - outbound `sendMessage` plus inbound `getUpdates`/`deleteWebhook`
for the long-polling command loop (`core/telegram_bot/`, see
docs/adr/0012-telegram-bot-polling.md).

Fixed vendor host (api.telegram.org) - not user-supplied - so this
intentionally does not go through app.core.security.ssrf_guard.safe_get; only
the bot token (path segment) and chat_id/text (body) are user-configured, never
the host. See backend/tests/core/test_ssrf_guard_coverage.py's
ALLOWLISTED_FIXED_HOST_FILES.

The bot token appears in the request URL's path, so `TelegramDeliveryError`
below deliberately never embeds the underlying httpx exception's str()/repr()
(which would include the full URL) or chains to it (`raise ... from None`) -
only the safe bits (status code, exception class name) are surfaced, so there
is nothing to leak into data/logs/*.log via log_redaction.py's usual
"log whatever exception escaped" path.
"""

from typing import Any

import httpx

_TIMEOUT = httpx.Timeout(10.0)
_API_BASE = "https://api.telegram.org"


class TelegramDeliveryError(Exception):
    """Raised when a Telegram message could not be delivered. Callers that must
    not let a Telegram outage propagate (e.g. alerts_service.raise_alert)
    should catch this themselves - it is not swallowed here so the one caller
    that does want to surface delivery failures (the settings "send test
    message" endpoint) can."""


async def _call(
    method: str, bot_token: str, api_method: str, *, timeout: httpx.Timeout, **kwargs: Any
) -> httpx.Response:
    """Issue one Telegram Bot API call, mapping any failure to
    `TelegramDeliveryError` - shared by every function below so the
    never-leak-the-token-bearing-URL handling (see module docstring) lives in
    exactly one place."""
    url = f"{_API_BASE}/bot{bot_token}/{api_method}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as e:
        raise TelegramDeliveryError(
            f"Telegram API returned HTTP {e.response.status_code}"
        ) from None
    except httpx.HTTPError as e:
        raise TelegramDeliveryError(f"Could not reach Telegram: {type(e).__name__}") from None


async def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    """Send a plain-text message via the Telegram Bot API's `sendMessage` method."""
    await _call(
        "POST", bot_token, "sendMessage", timeout=_TIMEOUT, json={"chat_id": chat_id, "text": text}
    )


async def get_updates(bot_token: str, offset: int, timeout: int) -> list[dict[str, Any]]:
    """Long-poll the Telegram Bot API's `getUpdates` method for new inbound messages.

    `timeout` is a Bot API long-poll parameter (server holds the connection open up to
    that many seconds waiting for an update), so the HTTP client's own timeout must be
    longer than it, not equal to it - otherwise a quiet period spuriously reads as a
    connection failure right at the moment `timeout` would have returned an empty batch.
    """
    response = await _call(
        "GET",
        bot_token,
        "getUpdates",
        timeout=httpx.Timeout(timeout + 10.0),
        params={"offset": offset, "timeout": timeout},
    )
    return response.json().get("result", [])


async def delete_webhook(bot_token: str) -> None:
    """Clear any webhook previously configured for this bot token.

    `getUpdates` (long-polling) and a webhook are mutually exclusive in the Bot API - a
    token that was ever webhook-configured elsewhere would otherwise make every
    `get_updates` call fail. Safe to call even when no webhook was ever set.
    """
    await _call("POST", bot_token, "deleteWebhook", timeout=_TIMEOUT)
