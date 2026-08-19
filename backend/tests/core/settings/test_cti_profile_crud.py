import pytest
from sqlalchemy import select

from app.core.settings.cti_profile.crud.cti_profile_crud import (
    create_cti_settings,
    delete_cti_settings,
    get_cti_settings,
    get_cti_settings_by_id,
    update_cti_settings,
)
from app.core.settings.cti_profile.models.cti_profile_models import CTIProfileSettings
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([CTIProfileSettings.__table__])


class TestGetCtiSettings:
    def test_returns_none_when_no_row_exists(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_cti_settings(db)

        assert _run(_scenario()) is None

    def test_returns_first_row_when_present(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_cti_settings(db, {"profile_name": "Alpha"})
                await db.commit()
            async with session_factory() as db:
                return await get_cti_settings(db)

        settings = _run(_scenario())
        assert settings.settings_data == {"profile_name": "Alpha"}


class TestGetCtiSettingsById:
    def test_returns_none_for_missing_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_cti_settings_by_id(db, 999)

        assert _run(_scenario()) is None

    def test_returns_matching_row(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_cti_settings(db, {"profile_name": "Alpha"})
                await db.commit()
                created_id = created.id
            async with session_factory() as db:
                return await get_cti_settings_by_id(db, created_id)

        settings = _run(_scenario())
        assert settings is not None
        assert settings.settings_data == {"profile_name": "Alpha"}


class TestCreateCtiSettings:
    def test_creates_row_with_given_data(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_cti_settings(db, {"profile_name": "Alpha"})
                await db.commit()
                return created

        created = _run(_scenario())
        assert created.id is not None
        assert created.settings_data == {"profile_name": "Alpha"}


class TestUpdateCtiSettings:
    def test_creates_row_when_none_exists(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                result = await update_cti_settings(db, {"profile_name": "New"})
                await db.commit()
                return result

        result = _run(_scenario())
        assert result.settings_data == {"profile_name": "New"}

    def test_updates_existing_row_instead_of_creating_a_second_one(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_cti_settings(db, {"profile_name": "Original"})
                await db.commit()

            async with session_factory() as db:
                await update_cti_settings(db, {"profile_name": "Updated"})
                await db.commit()

            async with session_factory() as db:
                rows = (await db.execute(select(CTIProfileSettings))).scalars().all()
                return rows

        rows = _run(_scenario())
        assert len(rows) == 1
        assert rows[0].settings_data == {"profile_name": "Updated"}


class TestDeleteCtiSettings:
    def test_deletes_existing_row_and_returns_true(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_cti_settings(db, {"profile_name": "Alpha"})
                await db.commit()
                created_id = created.id

            async with session_factory() as db:
                deleted = await delete_cti_settings(db, created_id)
                await db.commit()
                return deleted, created_id

        deleted, created_id = _run(_scenario())
        assert deleted is True

        async def _verify():
            async with session_factory() as db:
                return await get_cti_settings_by_id(db, created_id)

        assert _run(_verify()) is None

    def test_returns_false_for_missing_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_cti_settings(db, 999)

        assert _run(_scenario()) is False
