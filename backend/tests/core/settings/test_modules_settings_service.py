import pytest

from app.core.exceptions import ApplicationError
from app.core.settings.modules.models.modules_settings_models import ModuleSettings
from app.core.settings.modules.schemas.modules_settings_schemas import (
    ModuleSettingsCreate,
    ModuleSettingsUpdate,
    ModuleStatusUpdate,
)
from app.core.settings.modules.service.modules_settings_service import (
    create_new_module_setting,
    delete_module_setting_by_name,
    get_all_modules_settings,
    get_module_setting,
    update_module_setting,
    update_module_status,
)
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([ModuleSettings.__table__])


class TestGetAllModulesSettings:
    def test_returns_an_empty_list_when_none_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_all_modules_settings(db)

        assert _run(_scenario()) == []


class TestGetModuleSetting:
    def test_raises_a_404_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await get_module_setting(db, "newsfeed")

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 404

    def test_raises_a_400_for_an_invalid_name(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await get_module_setting(db, "mod;ule")

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 400

    def test_returns_the_matching_setting(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=True)
                )
                await db.commit()
            async with session_factory() as db:
                return await get_module_setting(db, "newsfeed")

        assert _run(_scenario()).enabled is True


class TestCreateNewModuleSetting:
    def test_creates_and_normalizes_the_name(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await create_new_module_setting(
                    db, ModuleSettingsCreate(name="NewsFeed", enabled=True)
                )

        result = _run(_scenario())
        assert result.name == "newsfeed"

    def test_rejects_a_duplicate_module_with_a_409(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=True)
                )
                await db.commit()
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=False)
                )

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 409


class TestUpdateModuleSetting:
    def test_raises_a_404_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_module_setting(db, "newsfeed", ModuleSettingsUpdate(enabled=False))

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 404

    def test_updates_the_enabled_status(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=True)
                )
                await db.commit()
            async with session_factory() as db:
                return await update_module_setting(
                    db, "newsfeed", ModuleSettingsUpdate(enabled=False)
                )

        assert _run(_scenario()).enabled is False

    def test_a_none_enabled_value_leaves_the_status_unchanged(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=True)
                )
                await db.commit()
            async with session_factory() as db:
                return await update_module_setting(db, "newsfeed", ModuleSettingsUpdate())

        assert _run(_scenario()).enabled is True


class TestUpdateModuleStatus:
    def test_creates_the_setting_when_it_does_not_exist_yet(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await update_module_status(db, "newsfeed", ModuleStatusUpdate(enabled=True))

        result = _run(_scenario())
        assert result.name == "newsfeed"
        assert result.enabled is True

    def test_updates_the_status_when_it_already_exists(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=True)
                )
                await db.commit()
            async with session_factory() as db:
                return await update_module_status(db, "newsfeed", ModuleStatusUpdate(enabled=False))

        assert _run(_scenario()).enabled is False


class TestDeleteModuleSettingByName:
    def test_raises_a_404_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await delete_module_setting_by_name(db, "newsfeed")

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 404

    def test_deletes_an_existing_setting(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_new_module_setting(
                    db, ModuleSettingsCreate(name="newsfeed", enabled=True)
                )
                await db.commit()
            async with session_factory() as db:
                await delete_module_setting_by_name(db, "newsfeed")
                await db.commit()
            async with session_factory() as db:
                return await get_all_modules_settings(db)

        assert _run(_scenario()) == []
