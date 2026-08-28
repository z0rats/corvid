import pytest

from app.core.exceptions import ApplicationError
from app.core.settings.keywords.models.keywords_settings_models import Keyword
from app.core.settings.keywords.schemas.keywords_settings_schemas import (
    KeywordCreate,
    KeywordUpdate,
)
from app.core.settings.keywords.service.keywords_settings_service import (
    create_keyword_service,
    delete_keyword_service,
    get_all_keywords,
    get_keyword_by_id_service,
    update_keyword_service,
)
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([Keyword.__table__])


class TestGetAllKeywords:
    def test_returns_an_empty_list_when_none_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_all_keywords(db)

        assert _run(_scenario()) == []

    def test_wraps_rows_into_response_schemas(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_keyword_service(db, KeywordCreate(keyword="malware"))
                await db.commit()
            async with session_factory() as db:
                return await get_all_keywords(db)

        results = _run(_scenario())
        assert results[0].keyword == "malware"
        assert results[0].id is not None


class TestGetKeywordByIdService:
    def test_raises_a_404_application_error_when_missing(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await get_keyword_by_id_service(db, 999)

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 404


class TestCreateKeywordService:
    def test_creates_and_normalizes_the_keyword(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await create_keyword_service(db, KeywordCreate(keyword="Malware"))

        result = _run(_scenario())
        assert result.keyword == "malware"

    def test_rejects_a_duplicate_keyword_with_a_400_application_error(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_keyword_service(db, KeywordCreate(keyword="malware"))
                await db.commit()
            async with session_factory() as db:
                await create_keyword_service(db, KeywordCreate(keyword="MALWARE"))

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 400

    def test_rejects_an_invalid_format_bypassing_schema_validation(self, session_factory):
        # KeywordCreate's own field_validator already rejects disallowed characters,
        # so this defensive check in the service is normally unreachable through the
        # HTTP layer - model_construct() skips validation to exercise it directly.
        invalid = KeywordCreate.model_construct(keyword="mal;ware")

        async def _scenario():
            async with session_factory() as db:
                await create_keyword_service(db, invalid)

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 400


class TestUpdateKeywordService:
    def test_raises_a_404_when_the_keyword_does_not_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await update_keyword_service(db, 999, KeywordUpdate(keyword="new"))

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 404

    def test_updates_the_keyword_value(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_keyword_service(db, KeywordCreate(keyword="old"))
                await db.commit()
                return created.id

        keyword_id = _run(_scenario())

        async def _update():
            async with session_factory() as db:
                return await update_keyword_service(db, keyword_id, KeywordUpdate(keyword="new"))

        assert _run(_update()).keyword == "new"

    def test_rejects_renaming_to_another_keywords_existing_value(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_keyword_service(db, KeywordCreate(keyword="alpha"))
                target = await create_keyword_service(db, KeywordCreate(keyword="beta"))
                await db.commit()
                return target.id

        target_id = _run(_scenario())

        async def _update():
            async with session_factory() as db:
                await update_keyword_service(db, target_id, KeywordUpdate(keyword="alpha"))

        with pytest.raises(ApplicationError) as exc_info:
            _run(_update())
        assert exc_info.value.status_code == 400

    def test_renaming_to_the_same_value_on_the_same_row_is_not_a_conflict(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_keyword_service(db, KeywordCreate(keyword="stable"))
                await db.commit()
                return created.id

        keyword_id = _run(_scenario())

        async def _update():
            async with session_factory() as db:
                return await update_keyword_service(db, keyword_id, KeywordUpdate(keyword="stable"))

        assert _run(_update()).keyword == "stable"


class TestDeleteKeywordService:
    def test_raises_a_404_when_the_keyword_does_not_exist(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await delete_keyword_service(db, 999)

        with pytest.raises(ApplicationError) as exc_info:
            _run(_scenario())
        assert exc_info.value.status_code == 404

    def test_deletes_and_returns_a_confirmation_detail(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_keyword_service(db, KeywordCreate(keyword="gone"))
                await db.commit()
                return created.id

        keyword_id = _run(_scenario())

        async def _delete():
            async with session_factory() as db:
                return await delete_keyword_service(db, keyword_id)

        assert _run(_delete())["detail"] == "Keyword deleted successfully"
