"""Live canaries for ru_business_check's sources: not "does our code work" (the fixture-based
suite covers that) but "did the site change its response shape". Each test calls the real
service against a reference ИНН whose record is long-lived and asserts the fields the parsers
and `flag_engine` rely on are non-empty.

Outcome policy - the reason this isn't just a smoke test:
  * schema drift (`… схема ответа изменилась …`) or an empty required field  -> FAIL. The
    production scan already reports such a source as not-checked rather than clean, but the
    parser needs fixing.
  * network/geo/anti-bot (timeout, 403/429/451, captcha)                     -> SKIP. The
    workflow runs from a GitHub runner (non-RU IP); some sources are expected to be
    unreachable from there, which says nothing about their schema.

Run: `cd backend && pytest -m canary -o addopts= -q` (see .github/workflows/canary.yml).
"""

import asyncio

import pytest

from app.features.ru_business_check.service.arbitration_service import fetch_arbitration_cases
from app.features.ru_business_check.service.cbr_warning_service import (
    LIST_URL as CBR_LIST_URL,
)
from app.features.ru_business_check.service.cbr_warning_service import (
    MIN_ENTRIES_WITH_INN,
    MIN_TOTAL_ENTRIES,
    parse_list,
)
from app.features.ru_business_check.service.disqualified_dump_service import (
    EXPECTED_HEADER,
    PORTAL,
    parse_dump,
    parse_meta,
)
from app.features.ru_business_check.service.disqualified_persons_service import check_disqualified
from app.features.ru_business_check.service.egrul_service import fetch_egrul_extract
from app.features.ru_business_check.service.fedresurs_service import fetch_fedresurs_status
from app.features.ru_business_check.service.fedsfm_service import check_terrorist_list
from app.features.ru_business_check.service.gir_bo_service import fetch_gir_bo_financials
from app.features.ru_business_check.service.msp_service import fetch_msp_status
from app.features.ru_business_check.service.ofac_sdn_service import (
    LIST_URL as OFAC_LIST_URL,
)
from app.features.ru_business_check.service.ofac_sdn_service import (
    MIN_ENTRIES_WITH_INN as OFAC_MIN_WITH_INN,
)
from app.features.ru_business_check.service.ofac_sdn_service import (
    MIN_TOTAL_ENTRIES as OFAC_MIN_TOTAL,
)
from app.features.ru_business_check.service.ofac_sdn_service import is_allowed_redirect, parse_sdn
from app.features.ru_business_check.service.pb_nalog_service import fetch_pb_nalog_profile
from app.features.ru_business_check.service.zakupki_rnp_service import fetch_rnp_entries
from tests.canary.policy import UNREACHABLE

pytestmark = pytest.mark.canary

# ПАО «Сбербанк»: in ЕГРЮЛ, Федресурс and Прозрачный бизнес, but a bank - absent from ГИР БО.
BANK_INN = "7707083893"
# АО «ДИКСИ ЮГ»: publishes statements in ГИР БО.
RETAILER_INN = "5036045205"


def _live(coro):
    """Run a live call: unreachable/blocked skips, any other failure fails."""
    try:
        return asyncio.run(coro)
    except ValueError as exc:
        if UNREACHABLE.search(str(exc)):
            pytest.skip(f"source unreachable/blocked from this network: {exc}")
        pytest.fail(f"{type(exc).__name__}: {exc}")
    except OSError as exc:  # pragma: no cover - raw socket errors that escape the clients
        pytest.skip(f"network error: {exc}")


def test_egrul_extract_has_the_fields_the_parser_and_flags_use():
    data, _ = _live(fetch_egrul_extract(BANK_INN))
    for field in ("full_name", "ogrn", "inn", "registration_date", "director_name"):
        assert data.get(field), f"ЕГРЮЛ extract lost {field}"


def test_fedresurs_status_and_publications():
    result, _ = _live(fetch_fedresurs_status(BANK_INN, is_individual=False))
    assert result["found"] is True
    assert result["status_text"], "Федресурс search row lost `status`"
    assert result["status_recognized"] is True, (
        f"Федресурс status vocabulary changed: {result['status_text']!r}"
    )
    assert result["publications_checked"] is True, result["publications_note"]
    # The bank publishes hundreds of creditor intents about *other* companies; none may be
    # attributed to the bank itself (role rule).
    assert not any(s["code"] == "creditor_bankruptcy_intent" for s in result["signals"])


def test_pb_nalog_resolves_the_entity():
    result, _ = _live(fetch_pb_nalog_profile(BANK_INN, is_individual=False))
    assert result["checked"] is True
    assert result["found"] is True


def test_rnp_feed_shape():
    # An empty result is fine; what must hold is that the RSS channel parses (drift raises).
    entries, raw = _live(fetch_rnp_entries(BANK_INN))
    assert "<channel" in raw
    assert isinstance(entries, list)


def test_gir_bo_statements_lines():
    result, _ = _live(fetch_gir_bo_financials(RETAILER_INN, is_individual=False))
    assert result["found"] is True and result["has_reports"] is True
    latest = result["years"][0]
    assert latest["detail_loaded"] is True
    for field in ("revenue", "assets", "equity", "current_assets", "current_liabilities"):
        assert latest[field] is not None, f"ГИР БО detail form lost {field}"


def test_gir_bo_absent_organization_is_a_normal_empty_result():
    result, _ = _live(fetch_gir_bo_financials(BANK_INN, is_individual=False))
    assert result["checked"] is True
    assert result["found"] is False


def test_arbitration_case_list_shape():
    # kad.arbitr.ru usually answers a non-RU IP with an anti-bot 451 (-> skip); when it
    # does answer, the Result/Items contract must hold.
    cases, _ = _live(fetch_arbitration_cases(BANK_INN))
    assert isinstance(cases, list)


def test_disqualified_registry_answers_with_rows_for_a_common_surname():
    # A regression guard for the silent-empty class: the registry answers JSON, and a
    # parser reading the wrong shape would report "no matches" for every name.
    result, _ = _live(check_disqualified("ИВАНОВ"))
    assert result["matched"] is True, "РДЛ returned no rows for a very common surname"
    assert result["matches"][0]["full_name"]
    assert result["matches"][0]["birth_date"]


def test_fedsfm_list_answers_with_the_expected_shape():
    result, raw = _live(check_terrorist_list("ЯЯЯЯЯЯЯЯЯ"))
    assert result["checked"] is True
    assert result["matched"] is False
    assert '"data"' in raw


def test_msp_register_answers_with_the_expected_shape():
    # A large company is normally not a МСП: `data: []` is fine; drift raises.
    result, raw = _live(fetch_msp_status(BANK_INN, is_individual=False))
    assert result["checked"] is True
    assert '"data"' in raw


def test_disqualified_dump_meta_and_csv_shape():
    import httpx

    def fetch(url):
        try:
            response = httpx.get(url, headers={"User-Agent": "Corvid-OSINT canary"}, timeout=60)
        except httpx.HTTPError as exc:
            pytest.skip(f"data.nalog.ru unreachable: {exc}")
        if response.status_code != 200:
            pytest.skip(f"data.nalog.ru HTTP {response.status_code}")
        return response.content.decode("utf-8-sig")

    url, dump_date, _ = parse_meta(fetch(f"{PORTAL}/meta.csv"))
    records = parse_dump(fetch(url))
    assert len(records) > 1000, f"suspiciously small dump ({len(records)} rows) for {dump_date}"
    assert EXPECTED_HEADER  # header equality is enforced inside parse_dump
    assert any(r["org_inn"] for r in records), "no record carries an organization ИНН any more"


def test_cbr_warning_list_shape_and_inn_coverage():
    import httpx

    try:
        response = httpx.get(
            CBR_LIST_URL, headers={"User-Agent": "Corvid-OSINT canary"}, timeout=90
        )
    except httpx.HTTPError as exc:
        pytest.skip(f"cbr.ru unreachable: {exc}")
    if response.status_code != 200:
        pytest.skip(f"cbr.ru HTTP {response.status_code}")
    records, total = parse_list(response.content.decode("utf-8-sig"))
    assert total >= MIN_TOTAL_ENTRIES, f"list shrank to {total} entries"
    assert len(records) >= MIN_ENTRIES_WITH_INN, "the list stopped carrying ИНН values"


def test_ofac_sdn_redirect_chain_and_tax_id_coverage():
    import httpx

    from app.features.ru_business_check.service.registry_dump_common import USER_AGENT

    try:
        with httpx.Client(timeout=90, follow_redirects=False) as client:
            url = OFAC_LIST_URL
            for _ in range(4):
                response = client.get(url, headers={"User-Agent": USER_AGENT})
                if response.status_code not in (301, 302, 303, 307, 308):
                    break
                url = str(response.next_request.url)
                assert is_allowed_redirect(url), (
                    f"OFAC now redirects outside the allowed hosts: {url[:80]}"
                )
    except httpx.HTTPError as exc:
        pytest.skip(f"OFAC unreachable: {exc}")
    if response.status_code != 200:
        pytest.skip(f"OFAC HTTP {response.status_code}")
    records, total = parse_sdn(response.content.decode("utf-8-sig"))
    assert total >= OFAC_MIN_TOTAL, f"list shrank to {total} entries"
    assert len(records) >= OFAC_MIN_WITH_INN, "SDN remarks stopped carrying Russian Tax ID values"
