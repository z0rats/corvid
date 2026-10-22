"""Every feature with a saved history (what the activity feed lists) either has a `RunSource`
in app/utils/run_source_registry.py - so its runs can be added to an investigation - or an
explicit reason in RUN_SOURCE_EXEMPT. A new scan feature fails here until it picks one."""

from app.features.activity.service.activity_service import activity_feature_names
from app.utils.run_source_registry import RUN_SOURCE_EXEMPT, RUN_SOURCES


def test_every_history_feature_has_a_run_source_or_exemption():
    features = set(activity_feature_names())
    missing = features - set(RUN_SOURCES) - set(RUN_SOURCE_EXEMPT)
    assert not missing, f"no RunSource or RUN_SOURCE_EXEMPT entry for: {sorted(missing)}"


def test_no_stale_or_contradictory_entries():
    features = set(activity_feature_names())
    assert not set(RUN_SOURCES) & set(RUN_SOURCE_EXEMPT)
    assert set(RUN_SOURCES) <= features, "RunSource for a feature the activity feed doesn't know"
    assert set(RUN_SOURCE_EXEMPT) <= features, "exemption for a feature that no longer exists"


def test_exemptions_give_a_reason():
    assert all(reason.strip() for reason in RUN_SOURCE_EXEMPT.values())


def test_run_source_keys_match_their_feature():
    assert all(key == source.feature for key, source in RUN_SOURCES.items())
