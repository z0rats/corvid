import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.settings.cti_profile.models.cti_profile_models import CTIProfileSettings
from app.core.settings.cti_profile.schemas.cti_profile_schemas import CTISettingsUpdate
from app.core.settings.cti_profile.service.cti_profile_service import (
    get_cti_profile_settings,
    update_cti_profile_settings,
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )


@pytest.fixture
def session_factory(engine):
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[CTIProfileSettings.__table__])

    _run(_create_tables())
    return async_sessionmaker(engine, expire_on_commit=False)


class TestGetCtiProfileSettings:
    def test_initializes_defaults_when_no_row_exists(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                result = await get_cti_profile_settings(db)
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.id == 1
        assert result.settings["profile_name"] == "Default CTI Profile"

    def test_reuses_existing_row_on_second_call(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                first = await get_cti_profile_settings(db)
                await db.commit()
            async with session_factory() as db:
                second = await get_cti_profile_settings(db)
                await db.commit()
                return first, second

        first, second = _run(_scenario())
        assert first.id == second.id


class TestUpdateCtiProfileSettings:
    def test_updates_settings_with_valid_data(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                result = await update_cti_profile_settings(
                    db, CTISettingsUpdate(settings={"profile_name": "My Profile", "severity_threshold": "high"}),
                )
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.settings["profile_name"] == "My Profile"
        assert result.settings["severity_threshold"] == "high"

    def test_rejects_missing_profile_name(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(db, CTISettingsUpdate(settings={}))

        with pytest.raises(ValueError, match="Missing required field: profile_name"):
            _run(_scenario())

    def test_rejects_empty_profile_name(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(db, CTISettingsUpdate(settings={"profile_name": "   "}))

        with pytest.raises(ValueError, match="non-empty string"):
            _run(_scenario())

    def test_rejects_non_string_profile_name(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(db, CTISettingsUpdate(settings={"profile_name": 123}))

        with pytest.raises(ValueError, match="non-empty string"):
            _run(_scenario())

    def test_rejects_invalid_severity_threshold(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(
                    db, CTISettingsUpdate(settings={"profile_name": "P", "severity_threshold": "extreme"}),
                )

        with pytest.raises(ValueError, match="Invalid severity threshold"):
            _run(_scenario())

    def test_rejects_non_list_indicators_of_interest(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(
                    db, CTISettingsUpdate(settings={"profile_name": "P", "indicators_of_interest": "ip_addresses"}),
                )

        with pytest.raises(ValueError, match="must be a list"):
            _run(_scenario())

    def test_allows_unsupported_ioc_type_but_only_warns(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                result = await update_cti_profile_settings(
                    db, CTISettingsUpdate(settings={"profile_name": "P", "indicators_of_interest": ["not_a_real_type"]}),
                )
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.settings["indicators_of_interest"] == ["not_a_real_type"]

    def test_rejects_non_dict_notification_preferences(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(
                    db, CTISettingsUpdate(settings={"profile_name": "P", "notification_preferences": "yes please"}),
                )

        with pytest.raises(ValueError, match="Notification preferences must be a dictionary"):
            _run(_scenario())

    def test_rejects_non_dict_email_preferences(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(
                    db,
                    CTISettingsUpdate(settings={
                        "profile_name": "P",
                        "notification_preferences": {"email": "enabled"},
                    }),
                )

        with pytest.raises(ValueError, match="Email preferences must be a dictionary"):
            _run(_scenario())

    def test_rejects_non_bool_email_enabled_flag(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(
                    db,
                    CTISettingsUpdate(settings={
                        "profile_name": "P",
                        "notification_preferences": {"email": {"enabled": "yes"}},
                    }),
                )

        with pytest.raises(ValueError, match="Email enabled flag must be a boolean"):
            _run(_scenario())

    def test_rejects_non_bool_webhook_enabled_flag(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_cti_profile_settings(
                    db,
                    CTISettingsUpdate(settings={
                        "profile_name": "P",
                        "notification_preferences": {"webhook": {"enabled": 1}},
                    }),
                )

        with pytest.raises(ValueError, match="Webhook enabled flag must be a boolean"):
            _run(_scenario())

    def test_accepts_valid_notification_preferences(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                result = await update_cti_profile_settings(
                    db,
                    CTISettingsUpdate(settings={
                        "profile_name": "P",
                        "notification_preferences": {"email": {"enabled": True}, "webhook": {"enabled": False}},
                    }),
                )
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.settings["notification_preferences"] == {
            "email": {"enabled": True}, "webhook": {"enabled": False},
        }
