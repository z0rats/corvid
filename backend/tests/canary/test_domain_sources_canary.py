"""Live canaries for domain_finder's keyless provider panels and the app's one-off keyless hosts
(Nominatim, PyPI, GitHub releases): "did the source change its response shape", not "does our
code work" (the mocked suite covers that). Assertions stick to the fields the consumers actually
read, never to counts.

Outcome policy: `policy.py`. domain_finder's clients raise `AppHTTPException`s whose
`<CODE>_TIMEOUT`/`_CONNECTION_ERROR`/`_RATE_LIMITED` (and a 403/429/451/5xx `_API_ERROR`) skip;
`_INVALID_RESPONSE` (a JSON endpoint answering HTML) fails - except crt.sh, which serves an HTML
error page when overloaded, so it gets a few retries and then skips.

Run: `cd backend && pytest -m canary -o addopts= -q` (see .github/workflows/canary.yml). A failing
weekly run opens (or comments on) a `canary-failure` GitHub issue; a new source needs an entry in
`coverage_map.py` (pinned by tests/core/test_canary_coverage.py).
"""

import os
import time

import pytest

from app.core import release_check
from app.core.exceptions import AppHTTPException
from app.core.utils.pypi_version_check import fetch_latest_pypi_version
from app.features.image_tools.service.reverse_geocode_service import _fetch_nominatim
from app.features.ioc_tools.domain_finder.service.certspotter_api_service import (
    fetch_certspotter_issuances,
)
from app.features.ioc_tools.domain_finder.service.crtsh_api_service import (
    fetch_crtsh_certificates,
)
from app.features.ioc_tools.domain_finder.service.hackertarget_api_service import (
    fetch_hackertarget_hosts,
)
from app.features.ioc_tools.domain_finder.service.rapiddns_api_service import (
    fetch_rapiddns_records,
)
from app.features.ioc_tools.domain_finder.service.rdap_api_service import fetch_rdap_domain_data
from app.features.ioc_tools.domain_finder.service.urlscan_api_service import (
    fetch_domain_scan_results,
)
from app.features.ioc_tools.domain_finder.service.wayback_api_service import (
    fetch_wayback_snapshots,
)
from tests.canary.policy import get, json_body, live

pytestmark = pytest.mark.canary

# IANA's reserved domain: certificates, archive captures, an RDAP record and URLScan scans that
# aren't going away.
DOMAIN = "example.com"
# RapidDNS has no rows for example.com; GitHub's zone has hundreds of passive-DNS records.
RAPIDDNS_DOMAIN = "github.com"
# The Eiffel Tower.
EIFFEL_TOWER = (48.8584, 2.2945)
PYPI_PACKAGE = "maigret"

CRTSH_ATTEMPTS = 3
CRTSH_RETRY_PAUSE_SECONDS = 5


def test_crtsh_certificates_carry_the_fields_ct_subdomains_reads():
    for attempt in range(CRTSH_ATTEMPTS):
        try:
            entries = live(fetch_crtsh_certificates(DOMAIN))
            break
        except AppHTTPException as exc:
            if exc.error_code != "CRTSH_INVALID_RESPONSE":
                raise
            if attempt + 1 < CRTSH_ATTEMPTS:
                time.sleep(CRTSH_RETRY_PAUSE_SECONDS)
    else:
        pytest.skip(f"crt.sh overload (known): HTML instead of JSON {CRTSH_ATTEMPTS} times")

    assert isinstance(entries, list) and entries, f"crt.sh returned no certificates for {DOMAIN}"
    for field in ("id", "issuer_name", "common_name", "name_value", "not_before", "not_after"):
        assert entries[0].get(field), f"crt.sh entries lost `{field}`"


def test_certspotter_issuances_carry_dns_names():
    page = live(fetch_certspotter_issuances(DOMAIN))

    assert page.issuances, f"Cert Spotter returned no issuances for {DOMAIN}"
    assert all(isinstance(issuance["dns_names"], list) for issuance in page.issuances)
    assert any(DOMAIN in issuance["dns_names"] for issuance in page.issuances)


def test_hackertarget_hostsearch_lines_are_host_ip_pairs():
    hosts = live(fetch_hackertarget_hosts(DOMAIN))

    assert hosts, f"HackerTarget answered with no `host,ip` lines for {DOMAIN}"
    for hostname, ip in hosts:
        assert hostname.endswith(DOMAIN), f"not a hostname: {hostname!r}"
        assert ip, f"HackerTarget line for {hostname} lost its IP"


def test_rapiddns_page_still_has_the_records_table():
    records = live(fetch_rapiddns_records(RAPIDDNS_DOMAIN))

    # The page answered 200 (anything else was skipped/failed above), so an empty result means
    # the `<tbody>` rows no longer have the shape the parser reads.
    assert records, f"RapidDNS page for {RAPIDDNS_DOMAIN} has no parsable records table"
    hostname, record_type, _address = records[0]
    assert hostname.endswith(RAPIDDNS_DOMAIN), f"hostname column moved: {records[0]!r}"
    assert record_type.isupper(), f"record-type column moved: {records[0]!r}"


def test_wayback_cdx_rows_carry_the_fields_the_snapshot_list_reads():
    entries = live(fetch_wayback_snapshots(DOMAIN))

    assert entries, f"Wayback CDX returned no captures for {DOMAIN}"
    for field in ("timestamp", "original", "statuscode", "mimetype"):
        assert field in entries[0], f"CDX header lost `{field}`"
    assert len(entries[0]["timestamp"]) == 14 and entries[0]["timestamp"].isdigit()


def test_rdap_bootstrap_redirect_reaches_a_registry_with_the_parsed_fields():
    data, rdap_server = live(fetch_rdap_domain_data(DOMAIN))

    assert rdap_server, "no answering RDAP server recovered from the request"
    actions = {event.get("eventAction") for event in data.get("events") or []}
    assert {"registration", "expiration"} <= actions, f"RDAP events changed: {actions}"
    assert any(ns.get("ldhName") for ns in data.get("nameservers") or [])
    assert isinstance(data.get("status"), list)
    registrar = next(
        (e for e in data.get("entities") or [] if "registrar" in (e.get("roles") or [])), None
    )
    assert registrar, "RDAP record lost its registrar entity"
    assert isinstance(registrar.get("vcardArray"), list), "registrar lost its vCard"
    assert any(p.get("type") == "IANA Registrar ID" for p in registrar.get("publicIds") or [])


def test_urlscan_domain_search_results_carry_the_fields_the_panel_reads():
    results = live(fetch_domain_scan_results(DOMAIN))

    assert results, f"URLScan.io returned no scans for {DOMAIN}"
    task, page = results[0].get("task") or {}, results[0].get("page") or {}
    for field in ("url", "time"):
        assert task.get(field), f"URLScan result `task` lost `{field}`"
    for field in ("url", "domain"):
        assert page.get(field), f"URLScan result `page` lost `{field}`"


def test_nominatim_reverse_geocodes_a_landmark_to_its_city():
    # Nominatim's usage policy: an identifying User-Agent (the service sends one) and at most
    # 1 request/s - this is one request a week.
    data = live(_fetch_nominatim(*EIFFEL_TOWER))

    display_name = data.get("display_name")
    assert display_name, "Nominatim response lost `display_name`"
    assert "Paris" in display_name, f"unexpected address: {display_name!r}"


def test_pypi_reports_the_latest_version_of_a_vendored_tool():
    # `fetch_latest_pypi_version` swallows every error into None, so read the raw shape first:
    # that tells "PyPI didn't answer" (skip) apart from "the JSON moved" (fail).
    info = json_body(get(f"https://pypi.org/pypi/{PYPI_PACKAGE}/json")).get("info") or {}
    assert info.get("version"), "PyPI JSON lost `info.version`"

    assert live(fetch_latest_pypi_version(PYPI_PACKAGE, timeout_seconds=30)) == info["version"]


def test_github_latest_release_has_a_tag_name():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set (the anonymous API rate limit is too low to rely on)")

    release = json_body(
        get(
            release_check.GITHUB_RELEASES_URL,
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"},
        )
    )
    assert str(release.get("tag_name", "")).startswith("v"), f"tag_name: {release.get('tag_name')}"
