"""Shared stand for the `run_scan_task` orchestration tests: fake settings/cached row and
helpers. Fixtures (`fake_db`, `captured`) live in this directory's `conftest.py`."""

import asyncio

from app.features.ru_business_check.service import ru_business_check_service as svc


def run(coro):
    return asyncio.run(coro)


class FakeSettings:
    fresh_registration_threshold_days = 365
    small_claim_amount_threshold = 100_000
    large_claim_amount_threshold = 1_000_000
    multiple_claims_defendant_threshold = 3
    mass_address_threshold = 10
    equity_ratio_threshold = 0.1
    current_ratio_threshold = 1.0
    revenue_drop_threshold = 0.5


class FakeCachedRow:
    resolved_inn = "7712345678"
    entity_type = "legal_entity"
    risk_level = "low"
    egrul_data = {"full_name": "cached co"}
    egrul_raw = "cached raw"
    disqualification_result = {
        "checked": True,
        "matched": False,
        "requires_manual_review": False,
        "matches": [],
    }
    disqualification_raw = "cached disq raw"
    arbitration_data = {"checked": True, "cases": []}
    arbitration_raw = "cached arbitration raw"
    fedresurs_data = {
        "checked": True,
        "found": False,
        "status_text": None,
        "is_active_bankruptcy": False,
        "profile_url": None,
    }
    fedresurs_raw = "cached fedresurs raw"
    pb_nalog_data = {
        "checked": True,
        "found": False,
        "mass_address_count": 0,
        "mass_address_companies": [],
        "profile_url": None,
    }
    pb_nalog_raw = "cached pb_nalog raw"
    fedsfm_result = {
        "checked": True,
        "matched": False,
        "requires_manual_review": False,
        "matches": [],
    }
    fedsfm_raw = "cached fedsfm raw"
    website = None
    rnp_data = {"checked": False, "entries": []}
    rnp_raw = "cached rnp raw"
    extra_data = {"gir_bo": {"checked": True, "found": False, "years": []}}
    extra_raw = {"gir_bo": "cached gir_bo raw"}
    raw_sha256 = {"egrul": "cached digest"}
    flags = []
    checked_sources = [
        "egrul",
        "disqualified_persons",
        "arbitration",
        "fedresurs",
        "pb_nalog",
        "fedsfm",
        "zakupki_rnp",
        "gir_bo",
        "msp",
        "disqualified_dump",
        "ofac_sdn",
        "cbr_warning",
    ]
    pending_sources = ["fssp"]
    candidates = []


def as_async(fn):
    async def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


def start(query="7712345678", force_refresh=False, website=None):
    run(
        svc.run_scan_task(
            query=query, force_refresh=force_refresh, website=website, queue=asyncio.Queue()
        )
    )
