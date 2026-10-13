import asyncio
import datetime
import json
from types import SimpleNamespace

import pytest

from app.features.newsfeed.models.newsfeed_models import NewsArticle
from app.features.newsfeed.schemas.newsfeed_schemas import ThreatIntelEnrichment
from app.features.newsfeed.service import article_analysis_service as svc

# The autouse fixture below stubs the lookup out for every test; one test needs the real one.
_REAL_LOAD_FEED_RELIABILITY = svc._load_feed_reliability


def _run(coro):
    return asyncio.run(coro)


def _async_return(value):
    async def _inner(*args, **kwargs):
        return value

    return _inner


def _async_raise(exc):
    async def _inner(*args, **kwargs):
        raise exc

    return _inner


def _make_article(analysis_result=None, mitre_attack=None):
    return NewsArticle(
        id=1,
        feedname="Test Feed",
        icon="default.png",
        title="Some cybersecurity article",
        summary="A short summary",
        full_text="Full article body with plenty of detail.",
        date=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        link="https://example.com/article",
        analysis_result=analysis_result,
        mitre_attack=mitre_attack,
    )


def _stored_analysis_json():
    return json.dumps({"markdown": "cached markdown", "raw": {"relevance": "Medium"}})


def _stored_mitre_json():
    return json.dumps(
        {
            "schema_version": "1.0",
            "has_mitre_data": True,
            "threat_actors": [],
            "targeted_sectors": [],
            "targeted_regions": [],
            "software": [],
            "ttps": [],
        }
    )


def _fresh_analysis_text():
    return json.dumps({"relevance": "High", "reason": "r", "summary": "s"})


def _enrichment(has_mitre_data=True):
    return ThreatIntelEnrichment(has_mitre_data=has_mitre_data)


@pytest.fixture(autouse=True)
def _patch_common(monkeypatch):
    """build_model_registry is always called once the cache-hit shortcut is bypassed."""
    monkeypatch.setattr(svc, "build_model_registry", _async_return({}))
    monkeypatch.setattr(svc, "_load_feed_reliability", _async_return(None))


class _Capture:
    def __init__(self):
        self.calls = []

    def fake_update(self):
        async def _inner(db, article_id, **kwargs):
            self.calls.append(kwargs)

        return _inner


def _patch_article(monkeypatch, article):
    monkeypatch.setattr(svc, "get_news_article_by_id", _async_return(article))


def _fail_if_called(name):
    async def _inner(*args, **kwargs):
        raise AssertionError(f"{name} should not have been called")

    return _inner


def _call(
    article_id=1,
    model_id="test-model",
    temperature=0.3,
    max_tokens=500,
    use_cti_settings=False,
    force=False,
    mode="all",
):
    return svc.analyze_article_with_llm(
        db=None,
        article_id=article_id,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        use_cti_settings=use_cti_settings,
        force=force,
        mode=mode,
    )


def test_both_cached_returns_cache_without_calling_llm(monkeypatch):
    article = _make_article(
        analysis_result=_stored_analysis_json(), mitre_attack=_stored_mitre_json()
    )
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _fail_if_called("execute_prompt"))
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _fail_if_called("enrich_article_with_mitre")
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="all", force=False))

    assert result["message"] == "Analysis already completed"
    assert result["analysis_result"] == {
        "markdown": "cached markdown",
        "raw": {"relevance": "Medium"},
    }
    assert result["mitre_attack"]["has_mitre_data"] is True
    assert capture.calls == []


def test_corrupt_cached_analysis_json_triggers_reanalysis(monkeypatch):
    article = _make_article(analysis_result="not valid json", mitre_attack=_stored_mitre_json())
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _async_return(_fresh_analysis_text()))
    monkeypatch.setattr(svc, "enrich_article_with_mitre", _async_return(_enrichment()))
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="all", force=False))

    assert result["message"] == "Analysis completed"
    assert result["analysis_result"]["raw"]["relevance"] == "High"
    assert len(capture.calls) == 1


def test_mode_analysis_only_does_not_touch_mitre(monkeypatch):
    article = _make_article()
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _async_return(_fresh_analysis_text()))
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _fail_if_called("enrich_article_with_mitre")
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="analysis", force=False))

    assert result["analysis_result"]["raw"]["relevance"] == "High"
    assert len(capture.calls) == 1
    assert "mitre_attack" not in capture.calls[0]
    assert "analysis_result" in capture.calls[0]


def test_mode_mitre_only_not_cached_success_with_data(monkeypatch):
    article = _make_article()
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _fail_if_called("execute_prompt"))
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_return(_enrichment(has_mitre_data=True))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="mitre", force=False))

    assert len(capture.calls) == 1
    assert capture.calls[0]["mitre_attack"] is not None
    assert json.loads(capture.calls[0]["mitre_attack"])["has_mitre_data"] is True
    assert result["mitre_attack"]["has_mitre_data"] is True


def test_mode_mitre_only_not_cached_success_no_data(monkeypatch):
    article = _make_article()
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_return(_enrichment(has_mitre_data=False))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="mitre", force=False))

    assert len(capture.calls) == 1
    assert capture.calls[0]["mitre_attack"] is None
    assert result["mitre_attack"] is None


def test_mitre_refresh_failure_does_not_wipe_cached_value(monkeypatch):
    """Regression test: a failed forced MITRE refresh must not blank out a valid cached value."""
    article = _make_article(mitre_attack=_stored_mitre_json())
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_raise(RuntimeError("upstream boom"))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="mitre", force=True))

    # Nothing to write: mode="mitre" only, and the refresh failed, so update_kwargs is empty.
    assert capture.calls == []
    assert result["mitre_attack"]["has_mitre_data"] is True


def test_mitre_refresh_success_no_longer_relevant_clears_cache(monkeypatch):
    """Legitimate case: a successful refresh that finds no MITRE relevance still clears the
    cache."""
    article = _make_article(mitre_attack=_stored_mitre_json())
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_return(_enrichment(has_mitre_data=False))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="mitre", force=True))

    assert len(capture.calls) == 1
    assert capture.calls[0]["mitre_attack"] is None
    assert result["mitre_attack"] is None


def test_all_mode_analysis_uncached_mitre_cached_concurrent_mitre_failure_preserves_cache(
    monkeypatch,
):
    """Main bug scenario: analysis is stale so both concurrent calls restart even though MITRE
    was already cached; when the fresh MITRE call fails, the old cached value must survive."""
    article = _make_article(analysis_result=None, mitre_attack=_stored_mitre_json())
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _async_return(_fresh_analysis_text()))
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_raise(RuntimeError("upstream boom"))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="all", force=False))

    assert len(capture.calls) == 1
    assert "mitre_attack" not in capture.calls[0]
    assert capture.calls[0]["analysis_result"] is not None
    assert result["analysis_result"]["raw"]["relevance"] == "High"
    assert result["mitre_attack"]["has_mitre_data"] is True


def test_all_mode_analysis_failure_aborts_before_any_write(monkeypatch):
    """Symmetric case: if analysis fails, nothing is written at all, including a successful
    concurrent MITRE result (known, accepted wasted-work behavior — not fixed here)."""
    article = _make_article(analysis_result=None, mitre_attack=_stored_mitre_json())
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _async_raise(RuntimeError("llm down")))
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_return(_enrichment(has_mitre_data=True))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    with pytest.raises(RuntimeError, match="llm down"):
        _run(_call(mode="all", force=False))

    assert capture.calls == []


def test_all_mode_nothing_cached_both_succeed(monkeypatch):
    article = _make_article()
    _patch_article(monkeypatch, article)
    monkeypatch.setattr(svc, "execute_prompt", _async_return(_fresh_analysis_text()))
    monkeypatch.setattr(
        svc, "enrich_article_with_mitre", _async_return(_enrichment(has_mitre_data=True))
    )
    capture = _Capture()
    monkeypatch.setattr(svc, "update_news_article", capture.fake_update())

    result = _run(_call(mode="all", force=False))

    assert len(capture.calls) == 1
    assert capture.calls[0]["analysis_result"] is not None
    assert capture.calls[0]["mitre_attack"] is not None
    assert result["analysis_result"]["raw"]["relevance"] == "High"
    assert result["mitre_attack"]["has_mitre_data"] is True


class TestSourceReliabilityInPrompt:
    ITEM = {"title": "T", "source": "Krebs", "date": "2026-01-01", "content": "body"}

    def test_graded_source_adds_the_admiralty_line_after_the_source(self):
        _, prompt = svc.build_analysis_prompts({**self.ITEM, "reliability": "B"}, "profile")
        assert "Source: Krebs\nSource reliability (Admiralty, A best to F): B\nDate:" in prompt

    @pytest.mark.parametrize("item", [ITEM, {**ITEM, "reliability": None}])
    def test_ungraded_source_adds_nothing(self, item):
        _, prompt = svc.build_analysis_prompts(item, "profile")
        assert "Admiralty" not in prompt
        assert "Source: Krebs\nDate:" in prompt

    def test_reliability_lookup_is_by_feed_name_and_tolerates_a_deleted_feed(self):
        class FakeDb:
            def __init__(self, feed):
                self.feed = feed

            async def get(self, model, key):
                assert key == "Krebs"
                return self.feed

        feed = SimpleNamespace(reliability="C")
        assert _run(_REAL_LOAD_FEED_RELIABILITY(FakeDb(feed), "Krebs")) == "C"
        assert _run(_REAL_LOAD_FEED_RELIABILITY(FakeDb(None), "Krebs")) is None
