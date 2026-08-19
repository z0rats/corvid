import pytest

from app.core.exceptions import ApplicationError
from app.core.settings.general.models.general_settings_models import GeneralSettings
from app.core.settings.general.schemas.general_settings_schemas import CommandPaletteSettingsUpdate
from app.core.settings.general.service.general_settings_service import (
    get_general_settings,
    update_command_palette_settings,
)
from app.core.settings.general.utils.validation_utils import validate_start_screen
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([GeneralSettings.__table__])


class TestGetGeneralSettingsDefaults:
    def test_creates_defaults_including_command_palette_fields(self, session_factory):
        async def _get():
            async with session_factory() as db:
                result = await get_general_settings(db)
                await db.commit()
                return result

        settings = _run(_get())

        assert settings.auto_open_on_single_match is True
        assert settings.start_screen == "search"
        assert settings.always_tiles is False


class TestUpdateCommandPaletteSettings:
    def test_updates_all_three_fields(self, session_factory):
        async def _update():
            async with session_factory() as db:
                result = await update_command_palette_settings(
                    db,
                    CommandPaletteSettingsUpdate(
                        auto_open_on_single_match=False,
                        start_screen="newsfeed",
                        always_tiles=True,
                    ),
                )
                await db.commit()
                return result

        settings = _run(_update())

        assert settings.auto_open_on_single_match is False
        assert settings.start_screen == "newsfeed"
        assert settings.always_tiles is True

    def test_partial_update_leaves_other_fields_untouched(self, session_factory):
        async def _seed_then_update():
            async with session_factory() as db:
                await update_command_palette_settings(
                    db,
                    CommandPaletteSettingsUpdate(always_tiles=True),
                )
                await db.commit()
            async with session_factory() as db:
                result = await update_command_palette_settings(
                    db,
                    CommandPaletteSettingsUpdate(start_screen="newsfeed"),
                )
                await db.commit()
                return result

        settings = _run(_seed_then_update())

        assert settings.start_screen == "newsfeed"
        assert settings.always_tiles is True
        assert settings.auto_open_on_single_match is True

    def test_creates_record_when_none_exists_yet(self, session_factory):
        async def _update():
            async with session_factory() as db:
                result = await update_command_palette_settings(
                    db,
                    CommandPaletteSettingsUpdate(start_screen="newsfeed"),
                )
                await db.commit()
                return result

        settings = _run(_update())

        assert settings.start_screen == "newsfeed"
        assert settings.auto_open_on_single_match is True
        assert settings.always_tiles is False

    def test_rejects_unsupported_start_screen_value(self, session_factory):
        async def _update():
            async with session_factory() as db:
                await update_command_palette_settings(
                    db,
                    CommandPaletteSettingsUpdate(start_screen="not-a-real-screen"),
                )

        with pytest.raises(ApplicationError):
            _run(_update())

    def test_start_screen_is_normalized_to_lowercase(self, session_factory):
        async def _update():
            async with session_factory() as db:
                result = await update_command_palette_settings(
                    db,
                    CommandPaletteSettingsUpdate(start_screen="NEWSFEED"),
                )
                await db.commit()
                return result

        settings = _run(_update())

        assert settings.start_screen == "newsfeed"


class TestValidateStartScreen:
    @pytest.mark.parametrize("value", ["search", "newsfeed", "SEARCH", " newsfeed "])
    def test_accepts_supported_values(self, value):
        assert validate_start_screen(value) is True

    @pytest.mark.parametrize("value", ["", None, "tiles", "home"])
    def test_rejects_unsupported_values(self, value):
        assert validate_start_screen(value) is False
