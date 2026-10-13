import asyncio
import datetime
import re
from types import SimpleNamespace

import pytest

from app.features.username_search.config.maigret_config import get_maigret_database
from app.features.username_search.routers import username_search_routes
from app.features.username_search.service import pivot_service
from app.features.username_search.service.pivot_service import (
    build_pivots,
    extract_emails,
    resolve_profile_link,
)


class TestKnownProfilesAreMaigretSites:
    def test_every_curated_site_name_exists_in_the_bundled_database(self):
        """A pivot's site name later drives a named single-site check, so it must be Maigret's
        exact name for that site."""
        names = {site.name for site in get_maigret_database().sites}
        missing = [site for site, _ in pivot_service._KNOWN_PROFILES if site not in names]
        assert missing == []


class TestResolveProfileLink:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://github.com/jsmith", ("GitHub", "jsmith")),
            ("https://www.github.com/jsmith/", ("GitHub", "jsmith")),
            ("https://x.com/jsmith?lang=en", ("Twitter", "jsmith")),
            ("https://twitter.com/jsmith", ("Twitter", "jsmith")),
            ("https://www.linkedin.com/in/jsmith/", ("LinkedIn", "jsmith")),
            ("https://www.youtube.com/@jsmith", ("YouTube", "jsmith")),
            ("https://www.instagram.com/jsmith/", ("Instagram", "jsmith")),
            ("https://www.reddit.com/user/jsmith", ("Reddit", "jsmith")),
            ("https://t.me/jsmith_bot", ("Telegram", "jsmith_bot")),
            ("https://medium.com/@jsmith", ("Medium", "jsmith")),
        ],
    )
    def test_known_platforms(self, url, expected):
        assert resolve_profile_link(url) == expected

    @pytest.mark.parametrize(
        "url",
        [
            "https://github.com/settings",  # a site page, not a person
            "https://github.com/jsmith/repo",  # deep path
            "https://www.instagram.com/jsmith/p/abc123",  # a post
            "https://jsmith.dev",  # personal root domain
            "https://bit.ly/abc",  # shorteners are dead ends
            "https://t.co/xyz",
            "javascript:alert(1)",
            "not a url",
            "ftp://github.com/jsmith",
        ],
    )
    def test_non_profiles_resolve_to_nothing(self, url):
        assert resolve_profile_link(url) is None

    def test_falls_back_to_the_maigret_database_for_other_sites(self):
        assert resolve_profile_link("https://habr.com/ru/users/jsmith/") == ("Habr", "jsmith")

    def test_database_templates_with_the_handle_as_a_subdomain_resolve_too(self):
        assert resolve_profile_link("https://jsmith.wix.com") == ("Wix", "jsmith")

    def test_a_greedy_database_template_cannot_capture_a_whole_path(self):
        # Pinterest-style `.+?` templates would otherwise yield the handle "jsmith/boards/x".
        assert resolve_profile_link("https://gitlab.com/jsmith/project/-/issues") is None


class _FakeSite:
    """Just the attributes pivot_service reads from a MaigretSite."""

    def __init__(self, name, url_main, url):
        self.name, self.url_main, self.url, self.url_subpath = name, url_main, url, ""
        self.disabled, self.type = False, "username"
        pattern = url.replace(".", r"\.").replace("{username}", "([a-z]+)")
        self.url_regexp = re.compile(f"^{pattern}$")

    def extract_id_from_url(self, url):
        match = self.url_regexp.match(url)
        return (match.group(1), "username") if match else None


class TestHostIndexFollowsTheDatabase:
    def test_a_replaced_database_is_not_served_from_the_old_index(self):
        first = SimpleNamespace(
            sites=[_FakeSite("Acme", "https://acme.test", "https://acme.test/u/{username}")]
        )
        second = SimpleNamespace(
            sites=[_FakeSite("Beta", "https://beta.test", "https://beta.test/u/{username}")]
        )

        assert resolve_profile_link("https://acme.test/u/bob", first) == ("Acme", "bob")
        assert resolve_profile_link("https://beta.test/u/bob", first) is None
        assert resolve_profile_link("https://beta.test/u/bob", second) == ("Beta", "bob")
        assert resolve_profile_link("https://acme.test/u/bob", second) is None


class TestExtractEmails:
    def test_keeps_personal_addresses_lowercased_and_deduplicated(self):
        assert extract_emails(["John <J@Mail.com>", "hello@acme.dev, j@mail.com"]) == [
            "j@mail.com",
            "hello@acme.dev",
        ]

    @pytest.mark.parametrize(
        "value",
        [
            "noreply@site.com",
            "postmaster@site.com",
            "someone@example.com",
            "someone@host.invalid",
            "12345+jsmith@users.noreply.github.com",
            None,
            42,
            "no address here",
        ],
    )
    def test_drops_role_placeholder_and_relay_addresses(self, value):
        assert extract_emails(value) == []


class TestBuildPivots:
    def test_merges_reported_handles_link_handles_names_and_emails(self):
        sites = [
            (
                "GitHub",
                {
                    "discovered_usernames": [
                        {"value": "JSmith_alt", "type": "username"},
                        {"value": "76561198000000000", "type": "steam_id"},
                    ],
                    "discovered_links": ["https://x.com/jsmith_x", "https://jsmith.dev"],
                    "discovered_names": ["John Smith"],
                    "discovered_emails": ["j@mail.com"],
                },
            ),
            (
                "Reddit",
                {
                    "discovered_usernames": [{"value": "jsmith_alt", "type": "username"}],
                    "discovered_links": ["https://x.com/jsmith_x"],
                    "discovered_names": ["john smith"],
                },
            ),
            ("Plain", None),
        ]

        pivots = build_pivots(sites, "jsmith")

        by_value = {u.value: u for u in pivots.usernames}
        assert by_value["JSmith_alt"].kind == "reported"
        assert by_value["JSmith_alt"].sites == ["GitHub", "Reddit"]
        assert by_value["jsmith_x"].kind == "link"
        assert by_value["jsmith_x"].site == "Twitter"
        assert by_value["jsmith_x"].sites == ["GitHub", "Reddit"]
        assert by_value["76561198000000000"].searchable is False
        assert [n.value for n in pivots.names] == ["John Smith"]
        assert pivots.names[0].sites == ["GitHub", "Reddit"]
        assert [e.value for e in pivots.emails] == ["j@mail.com"]

    def test_caps_each_list(self):
        many = [{"value": f"user{i}", "type": "username"} for i in range(80)]

        pivots = build_pivots([("A", {"discovered_usernames": many})], "jsmith")

        assert len(pivots.usernames) == pivot_service.MAX_PIVOTS_PER_KIND

    def test_excludes_the_searched_handle_even_when_reached_through_a_link(self):
        sites = [("Reddit", {"discovered_links": ["https://github.com/JSmith"]})]

        assert build_pivots(sites, "jsmith").usernames == []

    def test_a_handle_seen_both_ways_is_reported(self):
        sites = [
            ("A", {"discovered_links": ["https://github.com/other"]}),
            ("B", {"discovered_usernames": [{"value": "other", "type": "username"}]}),
        ]

        (only,) = build_pivots(sites, "jsmith").usernames

        assert (only.kind, only.sites, only.site) == ("reported", ["A", "B"], "GitHub")

    def test_ranks_searchable_reported_handles_first_and_opaque_ids_last(self):
        sites = [
            (
                "A",
                {
                    "discovered_usernames": [
                        {"value": "12345", "type": "vk_id"},
                        {"value": "plain", "type": "username"},
                    ],
                    "discovered_links": ["https://github.com/linked"],
                },
            )
        ]

        order = [u.value for u in build_pivots(sites, "jsmith").usernames]

        assert order == ["plain", "linked", "12345"]


def _run(coro):
    return asyncio.run(coro)


class TestRunDetailPivots:
    def test_run_detail_carries_pivots_computed_from_persisted_sites(self, monkeypatch):
        monkeypatch.setattr(username_search_routes, "has_scan_results", lambda _id: False)
        run = SimpleNamespace(
            id=1,
            username="jsmith",
            source="maigret",
            status="completed",
            total_sites_checked=10,
            found_count=1,
            error_message=None,
            tags=None,
            started_at=datetime.datetime(2026, 10, 5, tzinfo=datetime.UTC),
            completed_at=None,
            parent_search_id=None,
            site_results=[
                SimpleNamespace(
                    site_name="GitHub",
                    url_user="https://github.com/jsmith",
                    http_status=200,
                    extra={"discovered_links": ["https://x.com/jsmith_x"]},
                )
            ],
        )

        detail = _run(username_search_routes._run_detail(run, None))

        assert [(u.value, u.site) for u in detail.pivots.usernames] == [("jsmith_x", "Twitter")]

    def test_a_run_without_found_sites_has_empty_pivots(self, monkeypatch):
        monkeypatch.setattr(username_search_routes, "has_scan_results", lambda _id: False)
        run = SimpleNamespace(
            id=2,
            username="u",
            source="maigret",
            status="running",
            total_sites_checked=0,
            found_count=0,
            error_message=None,
            tags=None,
            started_at=datetime.datetime(2026, 10, 5, tzinfo=datetime.UTC),
            completed_at=None,
            parent_search_id=None,
            site_results=[],
        )

        detail = _run(username_search_routes._run_detail(run, None))

        assert detail.pivots.model_dump() == {"usernames": [], "names": [], "emails": []}

    @pytest.mark.parametrize(("parent", "exists"), [(SimpleNamespace(id=7), True), (None, False)])
    def test_run_detail_reports_whether_the_parent_run_still_exists(
        self, monkeypatch, parent, exists
    ):
        monkeypatch.setattr(username_search_routes, "has_scan_results", lambda _id: False)
        looked_up = []

        async def fake_get(db, search_id):
            looked_up.append(search_id)
            return parent

        monkeypatch.setattr(username_search_routes.USERNAME_SEARCH_SCANS.history, "get", fake_get)
        run = SimpleNamespace(
            id=8,
            username="u",
            source="maigret",
            status="completed",
            total_sites_checked=1,
            found_count=0,
            error_message=None,
            tags=None,
            started_at=datetime.datetime(2026, 10, 5, tzinfo=datetime.UTC),
            completed_at=None,
            parent_search_id=7,
            site_results=[],
        )

        detail = _run(username_search_routes._run_detail(run, None))

        assert looked_up == [7]
        assert detail.parent_exists is exists
