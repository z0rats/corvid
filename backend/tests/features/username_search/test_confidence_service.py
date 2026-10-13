import pytest

from app.features.username_search.service.confidence_service import (
    Anchors,
    annotate_confidence,
    build_anchors,
    classify_hit,
    name_key,
    personal_domain,
)

# What a parent run (searched "jsmith", found on GitHub) learned about its subject.
PARENT_SITES = [
    (
        "GitHub",
        {
            "discovered_names": ["John Smith, PhD"],
            "discovered_links": [
                "https://johnsmith.dev/about",
                "https://twitter.com/jsmith_dev",
                "https://bit.ly/abc",
            ],
            "discovered_emails": ["john@johnsmith.dev"],
        },
    )
]


@pytest.fixture
def anchors() -> Anchors:
    return build_anchors(PARENT_SITES, "jsmith")


class TestNameKey:
    def test_is_order_and_case_insensitive_and_stops_at_first_comma(self):
        assert name_key("John Smith, PhD", "x") == name_key("smith JOHN", "x")

    @pytest.mark.parametrize("name", ["", "  ", "jsmith", "J. Smith"])
    def test_a_name_restating_the_handle_carries_no_information(self, name):
        assert name_key(name, "jsmith") is None


class TestPersonalDomain:
    def test_own_site_is_a_personal_domain(self):
        assert personal_domain("https://www.johnsmith.dev/blog") == "johnsmith.dev"

    @pytest.mark.parametrize(
        "link",
        [
            "https://github.com/jsmith",
            "https://github.com/orgs/acme",
            "https://x.com/jsmith",
            "https://bit.ly/abc",
            "not a url",
        ],
    )
    def test_platforms_shorteners_and_junk_are_not(self, link):
        assert personal_domain(link) is None


class TestBuildAnchors:
    def test_collects_names_emails_domains_and_accounts(self, anchors):
        assert anchors.names == {name_key("John Smith", "jsmith")}
        assert anchors.emails == {"john@johnsmith.dev"}
        assert anchors.domains == {"johnsmith.dev"}
        assert ("twitter", "jsmith_dev") in anchors.pivot_accounts
        assert ("github", "jsmith") in anchors.known_accounts
        assert ("github", "jsmith") not in anchors.pivot_accounts


class TestClassifyHit:
    def test_confirmed_when_site_and_handle_are_a_published_link(self, anchors):
        assert classify_hit("Twitter", None, "jsmith_dev", anchors) == "confirmed"

    def test_same_handle_on_another_site_is_not_confirmed(self, anchors):
        assert classify_hit("Reddit", None, "jsmith_dev", anchors) == "candidate"

    @pytest.mark.parametrize(
        "extra",
        [
            {"discovered_names": ["Smith John"]},
            {"discovered_emails": ["john@johnsmith.dev"]},
            {"discovered_links": ["https://johnsmith.dev/"]},
            {"discovered_links": ["https://github.com/jsmith"]},
        ],
    )
    def test_likely_when_the_profile_echoes_an_anchor(self, anchors, extra):
        assert classify_hit("Reddit", extra, "jsmith_dev", anchors) == "likely"

    def test_conflicting_when_the_name_matches_no_anchor(self, anchors):
        extra = {"discovered_names": ["Maria Garcia"]}
        assert classify_hit("Reddit", extra, "jsmith_dev", anchors) == "conflicting"

    def test_a_name_restating_the_handle_is_not_a_conflict(self, anchors):
        extra = {"discovered_names": ["jsmith_dev"]}
        assert classify_hit("Reddit", extra, "jsmith_dev", anchors) == "candidate"

    def test_a_matching_anchor_beats_a_conflicting_second_name(self, anchors):
        extra = {"discovered_names": ["Maria Garcia", "John Smith"]}
        assert classify_hit("Reddit", extra, "jsmith_dev", anchors) == "likely"

    def test_without_anchor_names_a_name_cannot_conflict(self):
        anchors = build_anchors([("GitHub", {"discovered_emails": ["a@b.dev"]})], "jsmith")
        extra = {"discovered_names": ["Maria Garcia"]}
        assert classify_hit("Reddit", extra, "other", anchors) == "candidate"

    def test_bare_hit_is_a_candidate(self, anchors):
        assert classify_hit("Reddit", None, "jsmith_dev", anchors) == "candidate"


class TestAnnotateConfidence:
    def test_sets_confidence_without_dropping_other_extra_keys(self, anchors):
        rows = [
            {"site_name": "Twitter", "extra": {"discovered_names": ["x y"]}},
            {"site_name": "Reddit", "extra": None},
        ]
        annotate_confidence(rows, "jsmith_dev", anchors)
        assert rows[0]["extra"] == {"discovered_names": ["x y"], "confidence": "confirmed"}
        assert rows[1]["extra"] == {"confidence": "candidate"}
