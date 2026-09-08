"""Coverage for alerts_service.raise_alert - the single entrypoint every
notification-worthy event calls (see docs/adr/0011-telegram-notifications.md).
Exercises the DB row/WS broadcast/Telegram-delivery side effects directly
against an in-memory DB, with the WS manager and Telegram client mocked out.
"""

import pytest
from sqlalchemy import select

import app.core.alerts.service.alerts_service as alerts_service
from app.core.alerts.models.alerts_models import Alert
from app.core.alerts.service.alerts_service import raise_alert
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.core.settings.telegram.service.telegram_client import TelegramDeliveryError
from tests.conftest import run as _run


@pytest.fixture
def factory(make_session_factory):
    return make_session_factory([Alert.__table__, TelegramSettings.__table__])


@pytest.fixture
def broadcasts(monkeypatch):
    calls = []

    async def fake_broadcast(payload):
        calls.append(payload)

    monkeypatch.setattr(alerts_service.manager, "broadcast", fake_broadcast)
    return calls


@pytest.fixture
def telegram_calls(monkeypatch):
    calls = []

    async def fake_send(bot_token, chat_id, text):
        calls.append((bot_token, chat_id, text))

    monkeypatch.setattr(alerts_service, "send_telegram_message", fake_send)
    return calls


async def _seed_telegram_settings(factory, **fields):
    async with factory() as db:
        db.add(TelegramSettings(id=1, **fields))
        await db.commit()


async def _all_alerts(factory):
    async with factory() as db:
        result = await db.execute(select(Alert))
        return list(result.scalars().all())


class TestPlainAlert:
    def test_creates_row_and_broadcasts_without_telegram_category(
        self, factory, broadcasts, telegram_calls
    ):
        async def _scenario():
            async with factory() as db:
                alert = await raise_alert(db, "newsfeed", "title", "message")
                await db.commit()
            return alert

        alert = _run(_scenario())

        assert alert is not None
        assert alert.module == "newsfeed"
        assert len(broadcasts) == 1
        assert telegram_calls == []

    def test_truncates_message_to_column_limit(self, factory, broadcasts):
        async def _scenario():
            async with factory() as db:
                return await raise_alert(db, "mod", "title", "x" * 2000)

        alert = _run(_scenario())
        assert len(alert.message) == 1000


class TestScanFailedCategory:
    def test_always_notifies_when_telegram_enabled(self, factory, broadcasts, telegram_calls):
        _run(_seed_telegram_settings(factory, bot_token="t", chat_id="c", enabled=True))

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "email_search", "failed", "oops", telegram_category="scan_failed"
                )

        alert = _run(_scenario())
        assert alert is not None
        assert telegram_calls == [("t", "c", "failed\n\noops")]

    def test_no_telegram_call_when_disabled(self, factory, broadcasts, telegram_calls):
        _run(_seed_telegram_settings(factory, bot_token="t", chat_id="c", enabled=False))

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "email_search", "failed", "oops", telegram_category="scan_failed"
                )

        alert = _run(_scenario())
        assert alert is not None  # alert row still created
        assert telegram_calls == []

    def test_telegram_delivery_error_is_swallowed(self, factory, broadcasts, monkeypatch):
        _run(_seed_telegram_settings(factory, bot_token="t", chat_id="c", enabled=True))

        async def fake_send(bot_token, chat_id, text):
            raise TelegramDeliveryError("network down")

        monkeypatch.setattr(alerts_service, "send_telegram_message", fake_send)

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "email_search", "failed", "oops", telegram_category="scan_failed"
                )

        alert = _run(_scenario())
        assert alert is not None  # never raises out of raise_alert


class TestScanFinishedCategory:
    def test_muted_toggle_skips_the_alert_entirely(self, factory, broadcasts, telegram_calls):
        _run(
            _seed_telegram_settings(
                factory, bot_token="t", chat_id="c", enabled=True, notify_scan_events=False
            )
        )

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "git_recon", "done", "ok", telegram_category="scan_finished"
                )

        alert = _run(_scenario())
        assert alert is None
        assert broadcasts == []
        assert telegram_calls == []
        assert _run(_all_alerts(factory)) == []

    def test_enabled_toggle_creates_alert_and_notifies(self, factory, broadcasts, telegram_calls):
        _run(
            _seed_telegram_settings(
                factory, bot_token="t", chat_id="c", enabled=True, notify_scan_events=True
            )
        )

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "git_recon", "done", "ok", telegram_category="scan_finished"
                )

        alert = _run(_scenario())
        assert alert is not None
        assert telegram_calls == [("t", "c", "done\n\nok")]


class TestNewsfeedMatchCategory:
    def test_muted_toggle_skips_the_alert_entirely(self, factory, broadcasts, telegram_calls):
        _run(
            _seed_telegram_settings(
                factory, bot_token="t", chat_id="c", enabled=True, notify_newsfeed_matches=False
            )
        )

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "newsfeed", "match", "hit", telegram_category="newsfeed_match"
                )

        alert = _run(_scenario())
        assert alert is None
        assert broadcasts == []
        assert telegram_calls == []
        assert _run(_all_alerts(factory)) == []

    def test_enabled_toggle_creates_alert_and_notifies(self, factory, broadcasts, telegram_calls):
        _run(
            _seed_telegram_settings(
                factory, bot_token="t", chat_id="c", enabled=True, notify_newsfeed_matches=True
            )
        )

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "newsfeed", "match", "hit", telegram_category="newsfeed_match"
                )

        alert = _run(_scenario())
        assert alert is not None
        assert telegram_calls == [("t", "c", "match\n\nhit")]


class TestJobTransitionCategory:
    def test_alert_row_always_created_even_when_muted(self, factory, broadcasts, telegram_calls):
        """Unlike scan_finished, job_transition is edge-triggered and rare, so
        it always creates the in-app alert - only the Telegram push is muted."""
        _run(
            _seed_telegram_settings(
                factory, bot_token="t", chat_id="c", enabled=True, notify_job_failures=False
            )
        )

        async def _scenario():
            async with factory() as db:
                return await raise_alert(
                    db, "scheduler", "job failing", "oops", telegram_category="job_transition"
                )

        alert = _run(_scenario())
        assert alert is not None
        assert len(broadcasts) == 1
        assert telegram_calls == []
