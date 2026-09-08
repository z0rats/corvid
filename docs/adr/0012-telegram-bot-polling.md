# Inbound Telegram bot commands use long-polling, not a webhook

`docs/adr/0011-telegram-notifications.md` deferred inbound commands pending a
webhook-vs-polling decision. Corvid's default deployment has no public HTTPS endpoint -
`docker-compose.yaml`'s `backend` service exposes no port at all, only `frontend`'s nginx
does (port 4000). A Telegram webhook needs a public URL with a valid TLS certificate
reachable from Telegram's servers, which most self-hosters running this app behind a home
network or a bare VPS won't have. Long-polling (`getUpdates`) only needs outbound internet
access, which the backend already has (it already POSTs to `api.telegram.org` for
`sendMessage`). Polling is therefore the only option that works out of the box for this
app's deployment shape.

No bot-framework dependency (`python-telegram-bot`/`aiogram`) is added, for the same
reasoning as ADR 0011: `telegram_client.py` gets two more thin `httpx` functions
(`get_updates`, `delete_webhook`) alongside the existing `send_telegram_message`, rather
than pulling in a framework's own update-loop/dispatcher abstraction for three commands.

Command handling stays minimal and non-conversational: no per-user session state, no
multi-step flows. Each update is parsed and dispatched independently
(`core/telegram_bot/service/command_dispatcher.py`), and commands are processed
sequentially within the poll loop - a slow `/lookup` (its `asyncio.gather` fan-out across
IOC-lookup services can take tens of seconds) delays the next command's processing. This
is accepted for v1 given the single-user, low-message-frequency use case; a queue or
per-command concurrency would be premature.

This is the first persistent, gracefully-stoppable background task in this codebase.
`main.py`'s existing `asyncio.create_task(...)` calls (favicon fetch, blacklist backfill)
are fire-and-forget and run once at startup; the poll loop instead runs for the life of
the process, so `core/telegram_bot/service/polling_service.py` keeps its own task handle
and `stop_bot_polling()` is wired into `handle_application_shutdown` to cancel and await
it cleanly on container stop.

Inbound commands are a different trust boundary than outbound pushes - the bot now acts
on messages sent to it, gated only by matching the configured `chat_id` (anyone who
discovers the bot on Telegram before that check would otherwise be able to run lookups,
and read alert titles, through this Corvid instance). `TelegramSettings.bot_commands_enabled`
therefore defaults to `False`, unlike the existing outbound notification toggles which
default on.
