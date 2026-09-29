from app.features.image_tools.crud.geolocation_history_crud import (
    create_search,
    delete_search,
    get_search,
    list_searches,
)
from app.features.image_tools.models.geolocation_history_models import ImageGeolocationSearch
from app.features.image_tools.schemas.image_schemas import (
    GeoCandidate,
    GeoClue,
    ImageGeolocationResponse,
)
from tests.conftest import run


def _sample_result(location="Serbia", confidence=0.6) -> ImageGeolocationResponse:
    return ImageGeolocationResponse(
        candidates=[GeoCandidate(location=location, confidence=confidence, reasoning="clues")],
        clues=[GeoClue(category="signage_language", observation="Cyrillic", supports="Serbia")],
        caveats="Hypothesis only.",
        model_used="claude-sonnet-4-6",
    )


class TestCreateSearch:
    def test_persists_filename_hash_and_top_candidate(self, make_session_factory):
        session_factory = make_session_factory([ImageGeolocationSearch.__table__])

        async def _run():
            async with session_factory() as db:
                search = await create_search(db, "street.jpg", "a" * 64, _sample_result())
                await db.commit()
                return search

        search = run(_run())

        assert search.id is not None
        assert search.filename == "street.jpg"
        assert search.image_sha256 == "a" * 64
        assert search.model_used == "claude-sonnet-4-6"
        assert search.top_candidate == "Serbia"
        assert search.top_confidence == 0.6
        assert search.result["candidates"][0]["location"] == "Serbia"
        assert "model_used" not in search.result
        assert "history_id" not in search.result

    def test_leaves_top_candidate_null_when_no_candidates(self, make_session_factory):
        session_factory = make_session_factory([ImageGeolocationSearch.__table__])
        result = ImageGeolocationResponse(
            candidates=[], clues=[], caveats=None, model_used="claude-sonnet-4-6"
        )

        async def _run():
            async with session_factory() as db:
                return await create_search(db, "empty.jpg", "b" * 64, result)

        search = run(_run())

        assert search.top_candidate is None
        assert search.top_confidence is None


class TestListGetDeleteSearch:
    def test_list_returns_most_recent_first(self, make_session_factory):
        session_factory = make_session_factory([ImageGeolocationSearch.__table__])

        async def _run():
            async with session_factory() as db:
                first = await create_search(db, "first.jpg", "a" * 64, _sample_result())
                second = await create_search(db, "second.jpg", "b" * 64, _sample_result())
                await db.commit()
                return first, second, await list_searches(db)

        first, second, results = run(_run())

        assert [r.id for r in results] == [second.id, first.id]

    def test_get_returns_none_for_unknown_id(self, make_session_factory):
        session_factory = make_session_factory([ImageGeolocationSearch.__table__])

        async def _run():
            async with session_factory() as db:
                return await get_search(db, 999)

        assert run(_run()) is None

    def test_delete_removes_the_search(self, make_session_factory):
        session_factory = make_session_factory([ImageGeolocationSearch.__table__])

        async def _run():
            async with session_factory() as db:
                search = await create_search(db, "gone.jpg", "c" * 64, _sample_result())
                await db.commit()
                deleted = await delete_search(db, search.id)
                await db.commit()
                return search.id, deleted, await get_search(db, search.id)

        search_id, deleted, after = run(_run())

        assert deleted is not None
        assert deleted.id == search_id
        assert after is None

    def test_delete_returns_none_for_unknown_id(self, make_session_factory):
        session_factory = make_session_factory([ImageGeolocationSearch.__table__])

        async def _run():
            async with session_factory() as db:
                return await delete_search(db, 999)

        assert run(_run()) is None
