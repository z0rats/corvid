"""search_index: normalize() and the index built from SanctionsEntry rows."""

from app.features.sanctions_search.service.search_index import _build_index, normalize
from tests.conftest import run


def test_normalize_lowercases_strips_punctuation_and_accents_and_collapses_whitespace():
    assert normalize("  Jane   O'Doe-Smith! ") == "jane o doe smith"
    assert normalize("Škoda") == "skoda"
    assert normalize("") == ""


def test_normalize_is_idempotent_and_order_independent_for_whitespace():
    assert normalize("A  B") == normalize("A B") == normalize(" A B ")


def _seed(session_factory, entries):
    from app.features.sanctions_search.models.sanctions_search_models import SanctionsEntry

    async def _go():
        async with session_factory() as db:
            for e in entries:
                db.add(SanctionsEntry(**e))
            await db.commit()

    run(_go())


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


def test_build_index_indexes_names_and_aliases_normalized(monkeypatch, make_session_factory):
    import contextlib

    from app.features.sanctions_search.models.sanctions_search_models import SanctionsEntry
    from app.features.sanctions_search.service import search_index as idx

    session_factory = make_session_factory([SanctionsEntry.__table__])
    _seed(
        session_factory,
        [
            _entry(opensanctions_id="NK-1", name="Jane Doe", aliases=["J. Doe"]),
            _entry(
                opensanctions_id="NK-2",
                name="Acme Holdings",
                aliases=[],
                schema="Organization",
            ),
        ],
    )

    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with session_factory() as db:
            yield db

    monkeypatch.setattr(idx, "managed_session", fake_managed_session)

    index = run(_build_index())
    assert len(index.rows) == 2
    assert set(index.schemas) == {"Person", "Organization"}
    assert "jane doe" in index.exact_name
    assert "j doe" in index.exact_alias
    names = {name for name, _id in index.all_names}
    assert "jane doe" in names and "acme holdings" in names
