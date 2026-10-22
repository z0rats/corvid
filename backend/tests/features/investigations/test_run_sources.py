"""Each v1 feature's RunSource: report sections and graph entities from an unsaved run."""

import datetime

from app.features.email_search.models.email_search_models import MailSearch, MailSearchResult
from app.features.email_search.service.run_source import EMAIL_SEARCH_RUN_SOURCE
from app.features.ioc_tools.ioc_lookup.single_lookup.models.lookup_history_models import (
    SingleLookupResult,
    SingleLookupSearch,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.run_source import (
    IOC_LOOKUP_RUN_SOURCE,
)
from app.features.reddit_search.models.reddit_search_models import RedditSearch, RedditSearchResult
from app.features.reddit_search.service import run_source as reddit_run_source
from app.features.reddit_search.service.run_source import REDDIT_SEARCH_RUN_SOURCE
from app.features.username_search.models.username_search_models import (
    MaigretSearch,
    MaigretSiteResult,
)
from app.features.username_search.service.run_source import USERNAME_SEARCH_RUN_SOURCE

T0 = datetime.datetime(2026, 10, 1, 12, 0, tzinfo=datetime.UTC)


def _links(extraction):
    return {(link.source.id, link.relation, link.target.id) for link in extraction.links}


def _ioc(ioc, ioc_type, *results):
    return SingleLookupSearch(
        id=1,
        ioc=ioc,
        ioc_type=ioc_type,
        searched_at=T0,
        results=[
            SingleLookupResult(
                service_key=key,
                service_name=key,
                status=status,
                summary="s",
                tlp="WHITE",
                data=data,
            )
            for key, status, data in results
        ],
    )


def test_ioc_ip_extracts_asn_netblock_and_hostnames():
    search = _ioc(
        "1.1.1.1",
        "IPv4",
        ("ip_geo", "found", {"asn": "AS13335 Cloudflare, Inc."}),
        ("ip_rdap", "found", {"name": "APNIC-LABS", "cidrs": ["1.1.1.0/24"]}),
        ("internetdb", "found", {"hostnames": ["one.one.one.one"]}),
        ("virustotal", "found", {"asn": 99}),
    )

    out = IOC_LOOKUP_RUN_SOURCE.extract(search)

    assert out.root.id == "ip:1.1.1.1"
    assert _links(out) == {
        ("ip:1.1.1.1", "announced by", "asn:AS13335"),
        ("ip:1.1.1.1", "in netblock", "netblock:1.1.1.0/24"),
        ("ip:1.1.1.1", "hostname", "domain:one.one.one.one"),
    }


def test_ioc_email_extracts_breaches_gravatar_accounts_and_local_part():
    search = _ioc(
        "J.Doe@x.com",
        "Email",
        ("haveibeenpwned", "found", [{"Name": "LinkedIn"}, {"Title": "no name"}]),
        ("leakcheck", "found", {"found": 1, "fields": [], "sources": [{"name": "Canva"}]}),
        (
            "gravatar",
            "found",
            {
                "verified_accounts": [
                    {"label": "GitHub", "url": "https://github.com/jdoe", "username": "jdoe"},
                    {"label": "Site", "url": None},
                    {"label": "Odd", "url": 5},
                    "not an account",
                ]
            },
        ),
    )

    out = IOC_LOOKUP_RUN_SOURCE.extract(search)

    assert _links(out) == {
        ("email:j.doe@x.com", "local part", "username:j.doe"),
        ("email:j.doe@x.com", "breached in", "breach:linkedin"),
        ("email:j.doe@x.com", "breached in", "breach:canva"),
        ("email:j.doe@x.com", "linked account", "account:https://github.com/jdoe"),
        ("account:https://github.com/jdoe", "username", "username:jdoe"),
    }


def test_ioc_errored_or_unfound_results_add_nothing():
    search = _ioc(
        "1.1.1.1",
        "IPv4",
        ("ip_geo", "error", {"asn": "AS1"}),
        ("ip_rdap", "not_found", {"cidrs": ["1.0.0.0/8"]}),
        ("internetdb", "found", None),
    )
    assert IOC_LOOKUP_RUN_SOURCE.extract(search).links == []


def test_ioc_wallet_and_unknown_types():
    assert IOC_LOOKUP_RUN_SOURCE.extract(_ioc("0xAB", "EVMAddress")).root.id == "wallet:0xab"
    assert IOC_LOOKUP_RUN_SOURCE.extract(_ioc("???", "unknown")).root is None


def test_ioc_sections_are_the_single_export_sections():
    search = _ioc("1.1.1.1", "IPv4", ("ip_geo", "found", {}))
    titles = [s.title for s in IOC_LOOKUP_RUN_SOURCE.build_sections(search, "en")]
    assert titles == ["Search", "Service results"]
    assert IOC_LOOKUP_RUN_SOURCE.target(search) == "1.1.1.1"


def _maigret(*sites):
    return MaigretSearch(
        id=1,
        username="JDoe",
        source="maigret",
        status="completed",
        total_sites_checked=500,
        found_count=len(sites),
        started_at=T0,
        site_results=[MaigretSiteResult(site_name=name, url_user=url) for name, url in sites],
    )


def test_username_search_links_found_accounts():
    out = USERNAME_SEARCH_RUN_SOURCE.extract(_maigret(("GitHub", "https://github.com/JDoe")))
    assert _links(out) == {("username:jdoe", "account", "account:https://github.com/jdoe")}
    assert out.entities[1].label == "GitHub: JDoe"


def test_username_search_sections():
    sections = USERNAME_SEARCH_RUN_SOURCE.build_sections(
        _maigret(("GitHub", "https://github.com/JDoe")), "en"
    )
    assert [s.title for s in sections] == ["Username search", "Found accounts"]
    assert sections[1].rows[0].href == "https://github.com/JDoe"
    assert [s.title for s in USERNAME_SEARCH_RUN_SOURCE.build_sections(_maigret(), "en")] == [
        "Username search"
    ]


def _mail(source, target, *results):
    return MailSearch(
        id=1,
        username=target,
        source=source,
        status="completed",
        total_providers_checked=10,
        found_count=len(results),
        error_count=2,
        started_at=T0,
        provider_results=[
            MailSearchResult(provider_name=name, emails=emails) for name, emails in results
        ],
    )


def test_mailcat_run_links_username_to_mailboxes():
    out = EMAIL_SEARCH_RUN_SOURCE.extract(_mail("mailcat", "jdoe", ("Gmail", ["jdoe@gmail.com"])))
    assert _links(out) == {("username:jdoe", "mailbox", "email:jdoe@gmail.com")}


def test_user_scanner_run_links_email_to_services():
    out = EMAIL_SEARCH_RUN_SOURCE.extract(
        _mail("user_scanner", "jdoe@x.com", ("Spotify", ["jdoe@x.com"]))
    )
    assert _links(out) == {
        ("email:jdoe@x.com", "local part", "username:jdoe"),
        ("email:jdoe@x.com", "registered at", "account:spotify/jdoe@x.com"),
    }


def test_email_search_sections_flag_failed_checks():
    sections = EMAIL_SEARCH_RUN_SOURCE.build_sections(
        _mail("user_scanner", "jdoe@x.com", ("Spotify", [])), "en"
    )
    assert [s.title for s in sections] == ["Email search", "Registered at"]
    assert ("Checks failed (not checked)", "2") in [(r.label, r.value) for r in sections[0].rows]
    assert sections[1].rows[0].value == "-"


def _reddit(*items):
    return RedditSearch(
        id=1,
        username="JDoe",
        searched_at=T0,
        results=[
            RedditSearchResult(
                kind=kind,
                reddit_id=str(i),
                subreddit=sub,
                title="t" if kind == "post" else None,
                body="b" * 500,
                permalink=f"/r/{sub}/{i}",
                created_utc=1_700_000_000,
                removed=False,
                deleted=i == 0,
            )
            for i, (kind, sub) in enumerate(items)
        ],
    )


def test_reddit_links_user_to_busiest_subreddits(monkeypatch):
    monkeypatch.setattr(reddit_run_source, "TOP_SUBREDDITS", 1)
    out = REDDIT_SEARCH_RUN_SOURCE.extract(
        _reddit(("post", "python"), ("comment", "python"), ("comment", "rust"))
    )
    assert _links(out) == {("username:jdoe", "active in", "subreddit:python")}


def test_reddit_sections_summarize_and_truncate(monkeypatch):
    monkeypatch.setattr(reddit_run_source, "REPORT_ITEM_LIMIT", 1)
    sections = REDDIT_SEARCH_RUN_SOURCE.build_sections(
        _reddit(("comment", "python"), ("post", "rust")), "en"
    )
    assert [s.title for s in sections] == [
        "Reddit search",
        "Most active subreddits",
        "Newest 1 of 2 items",
    ]
    summary = {r.label: r.value for r in sections[0].rows}
    assert (summary["Posts"], summary["Comments"], summary["Removed or deleted"]) == ("1", "1", "1")
    item = sections[2].rows[0]
    assert item.href == "https://www.reddit.com/r/python/0"
    assert item.value.endswith("…") and len(item.value) <= 201
