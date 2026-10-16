"""Which live canary covers each external source - or why none does. Pinned by the normal suite
(`tests/core/test_canary_coverage.py`): a source that appears in one of the app's live registries
(ioc_lookup providers, domain_finder `Provider`s, ru_business_check sources, registry dumps, ...)
or behind a fixed-host HTTP client must have an entry here, so adding a source forces a decision
about its canary.

The unit is a *source*, not a file: `client_base.py` alone serves ~20 ioc_lookup providers.
Source ids are `<namespace>:<name>` for registry-derived sources and plain names for one-off hosts.
"""

from dataclasses import dataclass

from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS


@dataclass(frozen=True)
class Covered:
    test: str  # "<module in tests/canary>::<test function>"


@dataclass(frozen=True)
class Exempt:
    reason: str


EXEMPT_REASONS = {
    # Takes an API key the canary workflow doesn't have (yet).
    "needs-key",
    # Probing it acts on a real account (sign-in/recovery/registration flows can notify the
    # account owner) - see test_keyless_sources_canary.py's docstring.
    "acts-on-account",
    # Never leaves the host: a local model server or the app's own DB.
    "local-only",
    # Paid/enterprise-only access; no free tier to probe.
    "paid-enterprise",
    # Anonymous access is blocked or rate-limited too aggressively for a weekly check to say
    # anything about the response shape.
    "best-effort-anti-bot",
    # Keyless and probe-able, just without a canary so far.
    "no-canary-yet",
}

_KEYLESS = "test_keyless_sources_canary"
_IOC = "test_ioc_sources_canary"
_RU = "test_ru_business_check_canary"
_DOMAIN = "test_domain_sources_canary"


def _test(module: str, name: str) -> Covered:
    return Covered(f"{module}::{name}")


_DISQUALIFIED_DUMP = _test(_RU, "test_disqualified_dump_meta_and_csv_shape")
_CBR_WARNING = _test(_RU, "test_cbr_warning_list_shape_and_inn_coverage")
_OFAC_SDN = _test(_RU, "test_ofac_sdn_redirect_chain_and_tax_id_coverage")

COVERAGE: dict[str, Covered | Exempt] = {
    # --- ioc_lookup providers (service_registry keys) ---
    "ioc_lookup:abuseipdb": Exempt("needs-key"),
    "ioc_lookup:alienvault": Exempt("needs-key"),
    "ioc_lookup:blacklist": Exempt("local-only"),
    "ioc_lookup:checkphish": Exempt("needs-key"),
    "ioc_lookup:cisakev": _test(_IOC, "test_cisa_kev_lists_a_known_exploited_cve"),
    "ioc_lookup:crowdsec": Exempt("needs-key"),
    "ioc_lookup:crowdstrike": Exempt("paid-enterprise"),
    "ioc_lookup:emailrepio": Exempt("needs-key"),
    "ioc_lookup:ffraud": _test(_IOC, "test_ffraud_ip_lookup"),
    "ioc_lookup:ffraudemail": _test(_IOC, "test_ffraud_email_flags_a_disposable_domain"),
    "ioc_lookup:firstepss": _test(_IOC, "test_first_epss_scores_a_cve"),
    "ioc_lookup:github": Exempt("needs-key"),
    "ioc_lookup:haveibeenpwned": Exempt("paid-enterprise"),
    # The email/IP/domain endpoints; only the username one has a canary (hudson_rock:username).
    "ioc_lookup:hudsonrock": Exempt("no-canary-yet"),
    "ioc_lookup:hunterio": Exempt("needs-key"),
    "ioc_lookup:ipqualityscore": Exempt("needs-key"),
    "ioc_lookup:leakix": Exempt("needs-key"),
    "ioc_lookup:libraryofleaks": _test(_IOC, "test_library_of_leaks_returns_hit_counts"),
    "ioc_lookup:maltiverse": Exempt("needs-key"),
    "ioc_lookup:malwarebazaar": Exempt("needs-key"),
    "ioc_lookup:mandiant": Exempt("paid-enterprise"),
    "ioc_lookup:nistnvd": Exempt("needs-key"),
    "ioc_lookup:openphish": _test(_IOC, "test_openphish_feed_loads_and_matches_its_own_entries"),
    "ioc_lookup:pulsedive": Exempt("needs-key"),
    "ioc_lookup:reddit": Exempt("needs-key"),
    "ioc_lookup:safeBrowse": Exempt("needs-key"),
    "ioc_lookup:shodan": Exempt("needs-key"),
    "ioc_lookup:threatfox": Exempt("needs-key"),
    "ioc_lookup:twitter": Exempt("paid-enterprise"),
    "ioc_lookup:urlhaus": Exempt("needs-key"),
    "ioc_lookup:urlscanio": _test(_IOC, "test_urlscan_search_returns_scans"),
    "ioc_lookup:virustotal": Exempt("needs-key"),
    # --- domain_finder provider panels (`Provider.code`) ---
    "domain_finder:CRTSH": _test(
        _DOMAIN, "test_crtsh_certificates_carry_the_fields_ct_subdomains_reads"
    ),
    "domain_finder:DNSDUMPSTER": Exempt("needs-key"),
    "domain_finder:HACKERTARGET": _test(
        _DOMAIN, "test_hackertarget_hostsearch_lines_are_host_ip_pairs"
    ),
    "domain_finder:RAPIDDNS": _test(_DOMAIN, "test_rapiddns_page_still_has_the_records_table"),
    "domain_finder:RDAP": _test(
        _DOMAIN, "test_rdap_bootstrap_redirect_reaches_a_registry_with_the_parsed_fields"
    ),
    # domain_finder's own client, separate from the ioc_lookup `urlscanio` one.
    "domain_finder:URLSCAN": _test(
        _DOMAIN, "test_urlscan_domain_search_results_carry_the_fields_the_panel_reads"
    ),
    "domain_finder:WAYBACK": _test(
        _DOMAIN, "test_wayback_cdx_rows_carry_the_fields_the_snapshot_list_reads"
    ),
    # --- ru_business_check sources (AVAILABLE_SOURCES) ---
    "ru_business_check:egrul": _test(
        _RU, "test_egrul_extract_has_the_fields_the_parser_and_flags_use"
    ),
    "ru_business_check:disqualified_persons": _test(
        _RU, "test_disqualified_registry_answers_with_rows_for_a_common_surname"
    ),
    "ru_business_check:arbitration": _test(_RU, "test_arbitration_case_list_shape"),
    "ru_business_check:fedresurs": _test(_RU, "test_fedresurs_status_and_publications"),
    "ru_business_check:pb_nalog": _test(_RU, "test_pb_nalog_resolves_the_entity"),
    "ru_business_check:fedsfm": _test(_RU, "test_fedsfm_list_answers_with_the_expected_shape"),
    "ru_business_check:zakupki_rnp": _test(_RU, "test_rnp_feed_shape"),
    "ru_business_check:gir_bo": _test(_RU, "test_gir_bo_statements_lines"),
    "ru_business_check:msp": _test(_RU, "test_msp_register_answers_with_the_expected_shape"),
    "ru_business_check:disqualified_dump": _DISQUALIFIED_DUMP,
    "ru_business_check:ofac_sdn": _OFAC_SDN,
    "ru_business_check:cbr_warning": _CBR_WARNING,
    # --- core/registry_dumps jobs (DumpJob.source) ---
    "registry_dump:disqualified": _DISQUALIFIED_DUMP,
    "registry_dump:cbr_warning": _CBR_WARNING,
    "registry_dump:ofac_sdn": _OFAC_SDN,
    "registry_dump:opensanctions_ofac_sdn": _test(
        _KEYLESS, "test_opensanctions_sdn_dump_parses_above_the_floors"
    ),
    # --- address-blacklist feeds (blacklist_refresh_service.fetch_*_addresses) ---
    "address_blacklist:ofac": _test(_IOC, "test_blacklist_feed_yields_addresses"),
    "address_blacklist:scamsniffer": _test(_IOC, "test_blacklist_feed_yields_addresses"),
    "address_blacklist:opensanctions": _test(_IOC, "test_blacklist_feed_yields_addresses"),
    # --- default newsfeed RSS feeds: the canary is parametrized over DEFAULT_NEWSFEEDS itself ---
    **{
        f"newsfeed:{feed['name']}": _test(_IOC, "test_default_feed_serves_entries")
        for feed in DEFAULT_NEWSFEEDS
    },
    # --- dork_runner engines ---
    "dork_engine:duckduckgo": _test(_KEYLESS, "test_duckduckgo_html_results_are_organic_links"),
    "dork_engine:google": Exempt("best-effort-anti-bot"),
    "dork_engine:bing": Exempt("best-effort-anti-bot"),
    # --- phone_search checkers (sign-in/recovery flows) ---
    "phone_search:amazon_checker": Exempt("acts-on-account"),
    "phone_search:microsoft_checker": Exempt("acts-on-account"),
    "phone_search:facebook_checker": Exempt("acts-on-account"),
    # --- one-off fixed hosts (see FILE_SOURCES) ---
    "pypi": _test(_DOMAIN, "test_pypi_reports_the_latest_version_of_a_vendored_tool"),
    "github_releases": _test(_DOMAIN, "test_github_latest_release_has_a_tag_name"),
    "reddit_archive:arctic_shift": _test(
        _KEYLESS, "test_reddit_archive_returns_the_item_fields_reddit_search_reads"
    ),
    "reddit_archive:pullpush": _test(
        _KEYLESS, "test_reddit_archive_returns_the_item_fields_reddit_search_reads"
    ),
    "threat_actor_usernames": _test(_KEYLESS, "test_threat_actor_usernames_search_shape"),
    "hudson_rock:username": _test(_KEYLESS, "test_hudson_rock_username_search_shape"),
    "nominatim": _test(_DOMAIN, "test_nominatim_reverse_geocodes_a_landmark_to_its_city"),
    "chronoverify": Exempt("no-canary-yet"),
    "ollama": Exempt("local-only"),
    "youtube:oembed": _test(_KEYLESS, "test_youtube_oembed_metadata"),
    "youtube:page": _test(_KEYLESS, "test_youtube_page_metadata_scrape"),
    "youtube:data_api": Exempt("needs-key"),
    "steam:web_api": Exempt("needs-key"),
    "steam:community_locations": Exempt("no-canary-yet"),
    "steam:community_comments": Exempt("no-canary-yet"),
    "telegram": Exempt("needs-key"),
    # --- sources reached through a third-party library, not our own HTTP client ---
    "email_search:mailcat": Exempt("acts-on-account"),
    "email_search:user_scanner": Exempt("acts-on-account"),
    "email_search:ghunt": Exempt("acts-on-account"),
    "instagram": Exempt("best-effort-anti-bot"),
}

# Every file in test_ssrf_guard_coverage.ALLOWLISTED_FIXED_HOST_FILES -> the source ids it
# talks to. `<namespace>:*` stands for every source of a registry-derived namespace.
FILE_SOURCES: dict[str, tuple[str, ...]] = {
    "core/utils/pypi_version_check.py": ("pypi",),
    "features/ioc_tools/domain_finder/service/provider_http.py": ("domain_finder:*",),
    "features/ioc_tools/ioc_lookup/single_lookup/service/client_base.py": ("ioc_lookup:*",),
    "features/reddit_search/service/reddit_search_service.py": (
        "reddit_archive:arctic_shift",
        "reddit_archive:pullpush",
    ),
    "features/username_search/service/threat_actor_usernames_service.py": (
        "threat_actor_usernames",
    ),
    "features/username_search/service/hudson_rock_service.py": ("hudson_rock:username",),
    "features/dork_runner/service/engines/base.py": ("dork_engine:*",),
    # The quota endpoints of already-mapped keyed providers.
    "core/settings/api_keys/service/quota_clients.py": (
        "ioc_lookup:virustotal",
        "ioc_lookup:shodan",
        "ioc_lookup:hunterio",
    ),
    "core/release_check.py": ("github_releases",),
    "features/image_tools/service/reverse_geocode_service.py": ("nominatim",),
    "features/image_tools/service/chronoverify_api_service.py": ("chronoverify",),
    "utils/llm_service.py": ("ollama",),
    "features/youtube/service/youtube_oembed_service.py": ("youtube:oembed",),
    "features/youtube/service/youtube_page_service.py": ("youtube:page",),
    "features/youtube/service/youtube_api_service.py": ("youtube:data_api",),
    "features/steam_recon/service/steam_api_client.py": ("steam:web_api",),
    "features/steam_recon/service/steam_locations_service.py": ("steam:community_locations",),
    "features/steam_recon/service/steam_comments_service.py": ("steam:community_comments",),
    "features/ru_business_check/service/egrul_service.py": ("ru_business_check:egrul",),
    "features/ru_business_check/service/disqualified_persons_service.py": (
        "ru_business_check:disqualified_persons",
    ),
    "features/ru_business_check/service/arbitration_service.py": ("ru_business_check:arbitration",),
    "features/ru_business_check/service/fedresurs_service.py": ("ru_business_check:fedresurs",),
    "features/ru_business_check/service/pb_nalog_service.py": ("ru_business_check:pb_nalog",),
    "features/ru_business_check/service/fedsfm_service.py": ("ru_business_check:fedsfm",),
    "features/ru_business_check/service/zakupki_rnp_service.py": ("ru_business_check:zakupki_rnp",),
    "features/ru_business_check/service/gir_bo_service.py": ("ru_business_check:gir_bo",),
    "features/ru_business_check/service/msp_service.py": ("ru_business_check:msp",),
    "core/registry_dumps/common.py": ("registry_dump:*",),
    "core/settings/telegram/service/telegram_client.py": ("telegram",),
    "features/phone_search/service/phone_search_service.py": ("phone_search:*",),
}

# Allowlisted fixed-host files that talk to no source worth a canary, with the reason.
FILE_EXEMPT: dict[str, str] = {}

# Sources with no registry and no fixed-host file of our own (a third-party library does the
# HTTP) -> a module that must still exist, so a removed integration can't leave a stale entry.
LIBRARY_SOURCES: dict[str, str] = {
    "email_search:mailcat": "app.features.email_search.service.email_search_service",
    "email_search:user_scanner": "app.features.email_search.service.user_scanner_service",
    "email_search:ghunt": "app.features.email_search.service.ghunt_profile_service",
    "instagram": "app.features.instagram_search.service.instagram_common",
}
