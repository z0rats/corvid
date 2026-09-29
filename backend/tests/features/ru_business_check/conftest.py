import contextlib

import pytest

from app.features.ru_business_check.service import ru_business_check_service as svc
from tests.features.ru_business_check.scan_harness import FakeSettings
from tests.features.ru_business_check.scan_harness import as_async as _async


@pytest.fixture
def fake_db(monkeypatch):
    @contextlib.asynccontextmanager
    async def fake_managed_session():
        yield object()

    monkeypatch.setattr(svc, "managed_session", fake_managed_session)
    monkeypatch.setattr(svc, "get_ru_business_check_settings", _async(lambda db: FakeSettings()))
    # Safe default so a test that doesn't care about arbitration/fedresurs never makes a
    # real network call - tests exercising that wiring override these explicitly.
    monkeypatch.setattr(svc, "fetch_arbitration_cases", _async(lambda inn: ([], "")))
    monkeypatch.setattr(
        svc,
        "fetch_fedresurs_status",
        _async(
            lambda inn, is_individual: (
                {
                    "checked": True,
                    "found": False,
                    "status_text": None,
                    "is_active_bankruptcy": False,
                    "profile_url": None,
                },
                "",
            )
        ),
    )
    monkeypatch.setattr(
        svc,
        "fetch_pb_nalog_profile",
        _async(
            lambda inn, is_individual: (
                {
                    "checked": True,
                    "found": False,
                    "mass_address_count": 0,
                    "mass_address_companies": [],
                    "profile_url": None,
                },
                "",
            )
        ),
    )
    monkeypatch.setattr(
        svc,
        "check_terrorist_list",
        _async(
            lambda name: (
                {
                    "checked": True,
                    "matched": False,
                    "requires_manual_review": False,
                    "matches": [],
                },
                "",
            )
        ),
    )
    monkeypatch.setattr(svc, "fetch_rnp_entries", _async(lambda inn: ([], "")))
    monkeypatch.setattr(
        svc,
        "fetch_gir_bo_financials",
        _async(
            lambda inn, is_individual: (
                {"checked": True, "found": False, "has_reports": False, "years": []},
                "",
            )
        ),
    )
    monkeypatch.setattr(
        svc,
        "fetch_msp_status",
        _async(lambda inn, is_individual: ({"checked": True, "found": False}, "")),
    )
    monkeypatch.setattr(
        svc,
        "lookup_dump",
        _async(
            lambda db, inn, director_name: {
                "checked": True,
                "director_confirmed": False,
                "director_records": [],
                "company_records": [],
            }
        ),
    )
    monkeypatch.setattr(
        svc,
        "lookup_cbr_list",
        _async(lambda db, inn: {"checked": True, "as_of": "2026-09-28", "records": []}),
    )
    monkeypatch.setattr(
        svc,
        "lookup_ofac_list",
        _async(lambda db, inn: {"checked": True, "as_of": "2026-09-28", "records": []}),
    )
    return fake_managed_session


@pytest.fixture
def captured(monkeypatch):
    captured = {}

    async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
        captured.update(
            feature_name=feature_name, model=model, run_work=run_work, on_event=on_event, **kwargs
        )

    monkeypatch.setattr(svc.ScanRun, "execute", fake_execute)
    return captured
