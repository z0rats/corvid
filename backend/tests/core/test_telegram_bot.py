"""Coverage for core/telegram_bot/: command_dispatcher's chat_id security boundary,
each commands.py handler against a fixture DB, and polling_service's single-iteration
body (never the infinite loop, and never real network - httpx/telegram_client
functions are always mocked). See docs/adr/0012-telegram-bot-polling.md.
"""

from datetime import UTC, datetime, timedelta

import pytest

import app.core.telegram_bot.service.command_dispatcher as command_dispatcher
import app.core.telegram_bot.service.commands as commands
import app.core.telegram_bot.service.polling_service as polling_service
from app.core.alerts.models.alerts_models import Alert
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import LookupStatus, ServiceInfo
from tests.conftest import run as _run


def _settings(**overrides) -> TelegramSettings:
    fields = {
        "bot_token": "123:abc",
        "chat_id": "42",
        "enabled": True,
        "bot_commands_enabled": True,
        "web_base_url": "",
    }
    fields.update(overrides)
    return TelegramSettings(**fields)


def _update(chat_id, text) -> dict:
    return {"update_id": 1, "message": {"chat": {"id": chat_id}, "text": text}}


class TestHandleHelp:
    def test_lists_all_three_commands(self):
        reply = commands.handle_help()
        assert "/lookup" in reply
        assert "/digest" in reply
        assert "/help" in reply


class TestHandleDigest:
    @pytest.fixture
    def factory(self, make_session_factory):
        return make_session_factory([Alert.__table__])

    def test_no_unread_alerts(self, factory):
        async def scenario():
            async with factory() as db:
                return await commands.handle_digest(db)

        reply = _run(scenario())
        assert reply == "No unread alerts."

    def test_lists_unread_newest_first_and_skips_read(self, factory):
        now = datetime.now(UTC)

        async def scenario():
            async with factory() as db:
                db.add(
                    Alert(
                        module="scheduler",
                        title="Old failure",
                        message="m",
                        read=False,
                        timestamp=now,
                    )
                )
                db.add(
                    Alert(
                        module="scans",
                        title="Already read",
                        message="m",
                        read=True,
                        timestamp=now + timedelta(seconds=1),
                    )
                )
                db.add(
                    Alert(
                        module="newsfeed",
                        title="New match",
                        message="m",
                        read=False,
                        timestamp=now + timedelta(seconds=2),
                    )
                )
                await db.commit()
                return await commands.handle_digest(db)

        reply = _run(scenario())
        lines = reply.splitlines()
        assert "Already read" not in reply
        assert lines.index("[newsfeed] New match") < lines.index("[scheduler] Old failure")


class TestHandleLookup:
    @pytest.fixture
    def factory(self, make_session_factory):
        return make_session_factory([])

    def test_unknown_ioc_type(self, factory):
        async def scenario():
            async with factory() as db:
                return await commands.handle_lookup(db, "not a valid ioc!!", "")

        reply = _run(scenario())
        assert "Could not determine an IOC type" in reply

    def test_no_configured_services_for_type(self, factory, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VirusTotal",
                    supported_ioc_types=["Domain"],
                    is_configured=True,
                )
            ]

        monkeypatch.setattr(commands, "get_all_service_configs", fake_get_all_service_configs)

        async def scenario():
            async with factory() as db:
                return await commands.handle_lookup(db, "1.1.1.1", "")

        reply = _run(scenario())
        assert "No configured services support IOC type IPv4" in reply

    def test_formats_per_service_results_and_appends_web_link(self, factory, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VirusTotal",
                    supported_ioc_types=["IPv4"],
                    is_configured=True,
                ),
                ServiceInfo(
                    key="abuseipdb",
                    name="AbuseIPDB",
                    supported_ioc_types=["IPv4"],
                    is_configured=True,
                ),
                ServiceInfo(
                    key="shodan",
                    name="Shodan",
                    supported_ioc_types=["Domain"],  # not IPv4 - must be excluded
                    is_configured=True,
                ),
            ]

        async def fake_run_single_lookup(service_name, ioc, ioc_type, db, semaphore):
            if service_name == "virustotal":
                return {"status": LookupStatus.SUCCESS.value, "data": {}}
            return {"status": LookupStatus.RATE_LIMITED.value, "error": "rate limited"}

        monkeypatch.setattr(commands, "get_all_service_configs", fake_get_all_service_configs)
        monkeypatch.setattr(commands, "run_single_lookup_with_rate_limit", fake_run_single_lookup)

        async def scenario():
            async with factory() as db:
                return await commands.handle_lookup(db, "1.1.1.1", "https://corvid.example.com")

        reply = _run(scenario())
        assert "✅ VirusTotal" in reply
        assert "⚠️ AbuseIPDB: rate limited" in reply
        assert "Shodan" not in reply
        assert "https://corvid.example.com/ioc-tools/lookup?q=1.1.1.1" in reply

    def test_omits_web_link_when_base_url_not_set(self, factory, monkeypatch):
        async def fake_get_all_service_configs(db):
            return [
                ServiceInfo(
                    key="virustotal",
                    name="VirusTotal",
                    supported_ioc_types=["IPv4"],
                    is_configured=True,
                )
            ]

        async def fake_run_single_lookup(service_name, ioc, ioc_type, db, semaphore):
            return {"status": LookupStatus.SUCCESS.value, "data": {}}

        monkeypatch.setattr(commands, "get_all_service_configs", fake_get_all_service_configs)
        monkeypatch.setattr(commands, "run_single_lookup_with_rate_limit", fake_run_single_lookup)

        async def scenario():
            async with factory() as db:
                return await commands.handle_lookup(db, "1.1.1.1", "")

        reply = _run(scenario())
        assert "ioc-tools/lookup" not in reply


class TestHandleUpdateChatIdBoundary:
    def test_wrong_chat_id_is_silently_ignored(self, monkeypatch):
        sent = []

        async def fake_send(bot_token, chat_id, text):
            sent.append((bot_token, chat_id, text))

        monkeypatch.setattr(command_dispatcher, "send_telegram_message", fake_send)

        settings = _settings(chat_id="42")
        update = _update(chat_id=999, text="/help")

        _run(command_dispatcher._handle_update(update, settings))

        assert sent == []

    def test_matching_chat_id_is_handled(self, monkeypatch):
        sent = []

        async def fake_send(bot_token, chat_id, text):
            sent.append((bot_token, chat_id, text))

        monkeypatch.setattr(command_dispatcher, "send_telegram_message", fake_send)

        settings = _settings(chat_id="42")
        update = _update(chat_id=42, text="/help")

        _run(command_dispatcher._handle_update(update, settings))

        assert len(sent) == 1
        assert "/lookup" in sent[0][2]

    def test_non_message_update_is_ignored(self, monkeypatch):
        sent = []
        monkeypatch.setattr(command_dispatcher, "send_telegram_message", lambda *a: sent.append(a))

        _run(command_dispatcher._handle_update({"update_id": 1}, _settings()))

        assert sent == []


class TestDispatch:
    def test_unrecognized_command(self, monkeypatch):
        sent = []

        async def fake_send(bot_token, chat_id, text):
            sent.append(text)

        monkeypatch.setattr(command_dispatcher, "send_telegram_message", fake_send)

        settings = _settings()
        _run(command_dispatcher._handle_update(_update(42, "/frobnicate"), settings))

        assert sent == ["Unrecognized command. Try /help."]

    def test_strips_botname_suffix_in_groups(self, monkeypatch):
        sent = []

        async def fake_send(bot_token, chat_id, text):
            sent.append(text)

        monkeypatch.setattr(command_dispatcher, "send_telegram_message", fake_send)

        settings = _settings()
        _run(command_dispatcher._handle_update(_update(42, "/help@CorvidBot"), settings))

        assert "/lookup" in sent[0]

    def test_lookup_without_value_returns_usage(self, monkeypatch):
        sent = []

        async def fake_send(bot_token, chat_id, text):
            sent.append(text)

        monkeypatch.setattr(command_dispatcher, "send_telegram_message", fake_send)

        settings = _settings()
        _run(command_dispatcher._handle_update(_update(42, "/lookup"), settings))

        assert sent == ["Usage: /lookup <value>"]

    def test_lookup_sends_ack_before_result(self, monkeypatch):
        sent = []

        async def fake_send(bot_token, chat_id, text):
            sent.append(text)

        async def fake_handle_lookup(db, value, web_base_url):
            return "final result"

        monkeypatch.setattr(command_dispatcher, "send_telegram_message", fake_send)
        monkeypatch.setattr(command_dispatcher, "handle_lookup", fake_handle_lookup)

        settings = _settings()
        _run(command_dispatcher._handle_update(_update(42, "/lookup 1.1.1.1"), settings))

        assert sent == ["\U0001f50d Looking up...", "final result"]


class TestPollOnce:
    def test_idles_when_not_usable(self, monkeypatch):
        sleeps = []

        async def fake_sleep(seconds):
            sleeps.append(seconds)

        async def fake_get_settings():
            return _settings(enabled=False)

        monkeypatch.setattr(polling_service.asyncio, "sleep", fake_sleep)
        monkeypatch.setattr(polling_service, "_get_settings", fake_get_settings)

        offset, cleared = _run(polling_service._poll_once(0, None))

        assert offset == 0
        assert cleared is None
        assert sleeps == [polling_service._IDLE_SLEEP_SECONDS]

    def test_idles_when_bot_commands_disabled(self, monkeypatch):
        async def fake_get_settings():
            return _settings(bot_commands_enabled=False)

        async def fake_sleep(seconds):
            return None

        monkeypatch.setattr(polling_service.asyncio, "sleep", fake_sleep)
        monkeypatch.setattr(polling_service, "_get_settings", fake_get_settings)

        offset, cleared = _run(polling_service._poll_once(5, "123:abc"))

        assert offset == 5
        assert cleared == "123:abc"

    def test_processes_updates_and_advances_offset(self, monkeypatch):
        handled = []
        webhook_calls = []

        async def fake_get_settings():
            return _settings()

        async def fake_delete_webhook(bot_token):
            webhook_calls.append(bot_token)

        async def fake_get_updates(bot_token, offset, timeout):
            assert offset == 10
            return [
                {"update_id": 10, "message": {"chat": {"id": 42}, "text": "/help"}},
                {"update_id": 11, "message": {"chat": {"id": 42}, "text": "/digest"}},
            ]

        async def fake_handle_update(update, settings):
            handled.append(update["update_id"])

        monkeypatch.setattr(polling_service, "_get_settings", fake_get_settings)
        monkeypatch.setattr(polling_service, "delete_webhook", fake_delete_webhook)
        monkeypatch.setattr(polling_service, "get_updates", fake_get_updates)
        monkeypatch.setattr(polling_service, "_handle_update", fake_handle_update)

        offset, cleared = _run(polling_service._poll_once(10, None))

        assert offset == 12
        assert handled == [10, 11]
        assert webhook_calls == ["123:abc"]
        assert cleared == "123:abc"

    def test_does_not_reclear_webhook_for_same_token(self, monkeypatch):
        webhook_calls = []

        async def fake_get_settings():
            return _settings()

        async def fake_delete_webhook(bot_token):
            webhook_calls.append(bot_token)

        async def fake_get_updates(bot_token, offset, timeout):
            return []

        async def fake_handle_update(update, settings):
            pass

        monkeypatch.setattr(polling_service, "_get_settings", fake_get_settings)
        monkeypatch.setattr(polling_service, "delete_webhook", fake_delete_webhook)
        monkeypatch.setattr(polling_service, "get_updates", fake_get_updates)
        monkeypatch.setattr(polling_service, "_handle_update", fake_handle_update)

        _run(polling_service._poll_once(0, "123:abc"))

        assert webhook_calls == []
