import pytest

from app.core.settings.keywords.crud.keywords_settings_crud import (
    create_keyword_record,
    delete_keyword_record,
    get_keyword_by_id,
    get_keyword_by_value,
    get_keywords,
    get_keywords_count,
    get_keywords_list,
    keyword_exists,
    search_keywords,
    update_keyword_record,
)
from app.core.settings.keywords.models.keywords_settings_models import Keyword
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([Keyword.__table__])


class TestCreateAndGetKeywordRecord:
    def test_create_lowercases_the_stored_value(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_keyword_record(db, "Malware")
                await db.commit()
                return created.id

        keyword_id = _run(_scenario())

        async def _fetch():
            async with session_factory() as db:
                return await get_keyword_by_id(db, keyword_id)

        assert _run(_fetch()).keyword == "malware"

    def test_get_by_id_returns_none_for_missing_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_keyword_by_id(db, 999)

        assert _run(_scenario()) is None


class TestGetKeywordByValue:
    def test_lookup_is_case_insensitive(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_keyword_record(db, "phishing")
                await db.commit()
            async with session_factory() as db:
                return await get_keyword_by_value(db, "PHISHING")

        found = _run(_scenario())
        assert found is not None
        assert found.keyword == "phishing"

    def test_returns_none_when_absent(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await get_keyword_by_value(db, "absent")

        assert _run(_scenario()) is None


class TestKeywordExists:
    def test_true_when_present(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_keyword_record(db, "malware")
                await db.commit()
            async with session_factory() as db:
                return await keyword_exists(db, "malware")

        assert _run(_scenario()) is True

    def test_false_when_absent(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await keyword_exists(db, "absent")

        assert _run(_scenario()) is False


class TestGetKeywordsListAndCount:
    def test_pagination_limits_the_results(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for value in ["a", "b", "c"]:
                    await create_keyword_record(db, value)
                await db.commit()
            async with session_factory() as db:
                page = await get_keywords_list(db, skip=1, limit=1)
                total = await get_keywords_count(db)
                return page, total

        page, total = _run(_scenario())
        assert len(page) == 1
        assert total == 3

    def test_get_keywords_returns_everything_unpaginated(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                for value in ["a", "b"]:
                    await create_keyword_record(db, value)
                await db.commit()
            async with session_factory() as db:
                return await get_keywords(db)

        assert {k.keyword for k in _run(_scenario())} == {"a", "b"}


class TestUpdateAndDeleteKeywordRecord:
    def test_update_replaces_and_lowercases_the_value(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_keyword_record(db, "old")
                await db.commit()
                return created.id

        keyword_id = _run(_scenario())

        async def _update():
            async with session_factory() as db:
                existing = await get_keyword_by_id(db, keyword_id)
                await update_keyword_record(db, existing, "New")
                await db.commit()
            async with session_factory() as db:
                return await get_keyword_by_id(db, keyword_id)

        assert _run(_update()).keyword == "new"

    def test_delete_returns_true_and_removes_the_row(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                created = await create_keyword_record(db, "gone")
                await db.commit()
                return created.id

        keyword_id = _run(_scenario())

        async def _delete():
            async with session_factory() as db:
                deleted = await delete_keyword_record(db, keyword_id)
                await db.commit()
            async with session_factory() as db:
                remaining = await get_keyword_by_id(db, keyword_id)
                return deleted, remaining

        deleted, remaining = _run(_delete())
        assert deleted is True
        assert remaining is None

    def test_delete_returns_false_for_a_missing_id(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await delete_keyword_record(db, 999)

        assert _run(_scenario()) is False


class TestSearchKeywords:
    def test_finds_partial_matches(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                await create_keyword_record(db, "ransomware")
                await create_keyword_record(db, "malware")
                await create_keyword_record(db, "phishing")
                await db.commit()
            async with session_factory() as db:
                return await search_keywords(db, "ware")

        results = {k.keyword for k in _run(_scenario())}
        assert results == {"ransomware", "malware"}
