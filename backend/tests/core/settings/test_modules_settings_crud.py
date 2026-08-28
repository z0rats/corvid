import pytest

from app.core.settings.modules.crud.modules_settings_crud import (
    create_module_setting,
    delete_module_setting,
    get_all_module_settings,
    get_module_setting_by_name,
    module_setting_exists,
    update_module_setting_status,
)
from app.core.settings.modules.models.modules_settings_models import ModuleSettings
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([ModuleSettings.__table__])


class TestCreateModuleSetting:
    def test_defaults_enabled_status_when_omitted(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                setting = create_module_setting(db, "newsfeed")
                await db.commit()
                return setting.enabled

        assert _run(_scenario()) is True

    def test_uses_the_provided_enabled_status(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                setting = create_module_setting(db, "newsfeed", enabled=False)
                await db.commit()
                return setting.enabled

        assert _run(_scenario()) is False


class TestGetModuleSettingByName:
    def test_returns_none_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_module_setting_by_name(db, "absent")

        assert _run(_scenario()) is None

    def test_returns_the_matching_row(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                create_module_setting(db, "newsfeed", enabled=True)
                await db.commit()
            async with session_factory() as db:
                return await get_module_setting_by_name(db, "newsfeed")

        found = _run(_scenario())
        assert found is not None
        assert found.enabled is True


class TestModuleSettingExists:
    def test_true_when_present(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                create_module_setting(db, "newsfeed")
                await db.commit()
            async with session_factory() as db:
                return await module_setting_exists(db, "newsfeed")

        assert _run(_scenario()) is True

    def test_false_when_absent(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await module_setting_exists(db, "absent")

        assert _run(_scenario()) is False


class TestGetAllModuleSettings:
    def test_returns_every_row(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                create_module_setting(db, "newsfeed")
                create_module_setting(db, "image_tools")
                await db.commit()
            async with session_factory() as db:
                return await get_all_module_settings(db)

        names = {s.name for s in _run(_scenario())}
        assert names == {"newsfeed", "image_tools"}


class TestUpdateAndDeleteModuleSetting:
    def test_update_status_flips_enabled(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                create_module_setting(db, "newsfeed", enabled=True)
                await db.commit()
            async with session_factory() as db:
                existing = await get_module_setting_by_name(db, "newsfeed")
                update_module_setting_status(db, existing, False)
                await db.commit()
            async with session_factory() as db:
                return await get_module_setting_by_name(db, "newsfeed")

        assert _run(_scenario()).enabled is False

    def test_delete_removes_the_row(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                create_module_setting(db, "newsfeed")
                await db.commit()
            async with session_factory() as db:
                existing = await get_module_setting_by_name(db, "newsfeed")
                await delete_module_setting(db, existing)
                await db.commit()
            async with session_factory() as db:
                return await get_module_setting_by_name(db, "newsfeed")

        assert _run(_scenario()) is None
