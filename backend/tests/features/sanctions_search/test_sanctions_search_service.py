"""sanctions_search_service.search(): ranked matching, schema filter, truncation, and the
"list not loaded" guard - against a real (in-memory) SQLite DB, following the
tests/features/ru_business_check pattern of monkeypatching `managed_session` per-module rather
than mocking the DB away entirely, since the matching logic itself is what's under test here."""

import contextlib
import datetime

import pytest

from app.core.models.registry_dump import RegistryDump
from app.features.sanctions_search.models.sanctions_search_models import SanctionsEntry
from app.features.sanctions_search.service import sanctions_search_service as svc
from app.features.sanctions_search.service import search_index as idx
from tests.conftest import run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([SanctionsEntry.__table__, RegistryDump.__table__])


@pytest.fixture(autouse=True)
def _patch_managed_session(monkeypatch, session_factory):
    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with session_factory() as db:
            yield db

    monkeypatch.setattr(idx, "managed_session", fake_managed_session)
    idx.invalidate_index()
    yield
    idx.invalidate_index()


def _entry(**overrides):
    base = {
        "opensanctions_id": "NK-1",
        "schema": "Person",
        "name": "Jane Doe",
        "aliases": [],
        "countries": ["us"],
        "programs": ["US-GLOMAG"],
        "sanctions": None,
        "first_seen": None,
        "last_seen": None,
    }
    base.update(overrides)
    return base


def _seed(session_factory, entries, *, loaded=True):
    async def _go():
        async with session_factory() as db:
            for e in entries:
                db.add(SanctionsEntry(**e))
            if loaded:
                db.add(
                    RegistryDump(
                        source=svc.SOURCE_KEY,
                        dump_date=datetime.date(2026, 9, 29),
                        valid_until=None,
                        row_count=len(entries),
                        url=svc.LIST_URL,
                        refreshed_at=datetime.datetime.now(datetime.UTC),
                    )
                )
            await db.commit()

    run(_go())


def test_exact_name_ranks_above_substring_match(session_factory):
    _seed(
        session_factory,
        [
            _entry(opensanctions_id="NK-1", name="Jane Doe"),
            _entry(opensanctions_id="NK-2", name="Jane Doe Enterprises"),
        ],
    )

    async def _go():
        async with session_factory() as db:
            return await svc.search(db, query="Jane Doe", schema=None, limit=50)

    result = run(_go())
    assert [m["opensanctions_id"] for m in result["matches"]] == ["NK-1", "NK-2"]
    assert result["matches"][0]["matched_on"] == "exact_name"
    assert result["matches"][1]["matched_on"] == "substring_name"


def test_alias_match_is_reported_once_even_if_name_also_matches(session_factory):
    _seed(
        session_factory,
        [_entry(opensanctions_id="NK-1", name="Jane Doe", aliases=["Jane Doe", "J. Doe"])],
    )

    async def _go():
        async with session_factory() as db:
            return await svc.search(db, query="Jane Doe", schema=None, limit=50)

    result = run(_go())
    assert len(result["matches"]) == 1
    assert result["matches"][0]["matched_on"] == "exact_name"


def test_a_name_only_findable_via_its_alias_is_matched(session_factory):
    _seed(
        session_factory,
        [_entry(opensanctions_id="NK-1", name="Джейн Доу", aliases=["Jane Doe"])],
    )

    async def _go():
        async with session_factory() as db:
            return await svc.search(db, query="Jane Doe", schema=None, limit=50)

    result = run(_go())
    assert [m["opensanctions_id"] for m in result["matches"]] == ["NK-1"]
    assert result["matches"][0]["matched_on"] == "exact_alias"


def test_schema_filter_excludes_other_schemas(session_factory):
    _seed(
        session_factory,
        [
            _entry(opensanctions_id="NK-1", name="Acme Shipping", schema="Vessel"),
            _entry(opensanctions_id="NK-2", name="Acme Shipping Co", schema="Organization"),
        ],
    )

    async def _go():
        async with session_factory() as db:
            return await svc.search(db, query="Acme Shipping", schema="Vessel", limit=50)

    result = run(_go())
    assert [m["opensanctions_id"] for m in result["matches"]] == ["NK-1"]


def test_truncation_reports_total_matches_beyond_limit(session_factory):
    _seed(
        session_factory,
        [_entry(opensanctions_id=f"NK-{i}", name=f"Acme Corp {i}") for i in range(5)],
    )

    async def _go():
        async with session_factory() as db:
            return await svc.search(db, query="Acme Corp", schema=None, limit=2)

    result = run(_go())
    assert len(result["matches"]) == 2
    assert result["total_matches"] == 5
    assert result["truncated"] is True


def test_search_raises_when_the_list_was_never_loaded(session_factory):
    _seed(session_factory, [], loaded=False)

    async def _go():
        async with session_factory() as db:
            await svc.search(db, query="anything", schema=None, limit=50)

    with pytest.raises(svc.SanctionsSearchError):
        run(_go())


def test_list_schemas_returns_the_distinct_schemas_in_the_index(session_factory):
    _seed(
        session_factory,
        [
            _entry(opensanctions_id="NK-1", name="Jane Doe", schema="Person"),
            _entry(opensanctions_id="NK-2", name="Acme Corp", schema="Organization"),
        ],
    )
    assert run(svc.list_schemas()) == ["Organization", "Person"]
