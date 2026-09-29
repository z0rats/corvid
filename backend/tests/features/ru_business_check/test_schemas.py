import datetime

from app.features.ru_business_check.schemas.ru_business_check_schemas import SearchDetail


def _detail(**overrides):
    base = dict(
        id=1,
        query="7712345678",
        status="completed",
        searched_at=datetime.datetime(2026, 9, 28, tzinfo=datetime.UTC),
        checked_sources=["egrul", "zakupki_rnp"],
    )
    base.update(overrides)
    return SearchDetail(**base)


def test_missing_required_sources_lists_what_made_the_verdict_incomplete():
    detail = _detail(risk_level="incomplete")
    assert detail.missing_required_sources == ["fedresurs"]
    assert detail.model_dump()["missing_required_sources"] == ["fedresurs"]


def test_missing_required_sources_is_empty_for_a_complete_verdict():
    assert _detail(risk_level="low").missing_required_sources == []
