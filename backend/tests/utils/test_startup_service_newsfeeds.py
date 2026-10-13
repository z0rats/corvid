"""create_default_newsfeeds: seeding and one-time reliability grading of default feeds."""

from sqlalchemy import select

from app.features.newsfeed.models.newsfeed_models import NewsfeedSettings
from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS
from app.utils.startup_service import create_default_newsfeeds
from tests.conftest import run

GRADES = {"A", "B", "C", "D", "E", "F"}


def _grades(session_factory) -> dict[str, str | None]:
    async def _read():
        async with session_factory() as db:
            rows = (await db.execute(select(NewsfeedSettings))).scalars().all()
            return {row.name: row.reliability for row in rows}

    return run(_read())


def test_every_default_feed_has_a_valid_grade():
    assert all(feed["reliability"] in GRADES for feed in DEFAULT_NEWSFEEDS)


def test_fresh_install_seeds_graded_feeds(make_session_factory):
    session_factory = make_session_factory([NewsfeedSettings.__table__])

    async def _seed():
        async with session_factory() as db:
            await create_default_newsfeeds(db)
            await db.commit()

    run(_seed())

    assert _grades(session_factory) == {f["name"]: f["reliability"] for f in DEFAULT_NEWSFEEDS}


def test_grades_ungraded_default_feeds_but_keeps_user_grades(make_session_factory):
    session_factory = make_session_factory([NewsfeedSettings.__table__])
    first, second = DEFAULT_NEWSFEEDS[0], DEFAULT_NEWSFEEDS[1]

    async def _seed_then_run_twice():
        async with session_factory() as db:
            db.add(NewsfeedSettings(name=first["name"], url=first["url"]))
            db.add(NewsfeedSettings(name=second["name"], url=second["url"], reliability="E"))
            await db.commit()
        for _ in range(2):
            async with session_factory() as db:
                await create_default_newsfeeds(db)
                await db.commit()

    run(_seed_then_run_twice())

    grades = _grades(session_factory)
    assert grades[first["name"]] == first["reliability"]
    assert grades[second["name"]] == "E"
