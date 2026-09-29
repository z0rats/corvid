"""cbr_warning_service against the list shape captured live from cbr.ru on 2026-09-28
(`{"RC": [entry...]}`; entries trimmed and values synthetic)."""

import asyncio
import dataclasses
import datetime
import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select

from app.core.models.registry_dump import RegistryDump
from app.core.registry_dumps.common import is_stale, refresh_lock
from app.features.ru_business_check.models.ru_business_check_models import CbrWarningRecord
from app.features.ru_business_check.service import cbr_warning_service as svc
from app.features.ru_business_check.service import cbr_warning_service as svc_module
from app.features.ru_business_check.service.cbr_warning_service import (
    CbrWarningError,
    lookup_list,
    parse_list,
    refresh_list,
)

LIST_TEXT = (Path(__file__).parent / "fixtures" / "cbr_warning_list.json").read_text()
LIST = json.loads(LIST_TEXT)


async def _locked(refresh, db):
    """Refreshes must run under the source's lock (enforced by `replace_dump`)."""
    async with refresh_lock(svc_module.SOURCE_KEY):
        return await refresh(db)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _relaxed_floors(monkeypatch):
    # The real floors are sized for the ~27k-entry live list; the fixture is tiny.
    monkeypatch.setattr(
        svc, "SOURCE", dataclasses.replace(svc.SOURCE, min_total=1, min_matchable=1)
    )


class TestParseList:
    def test_keeps_only_entries_with_a_ten_digit_inn(self):
        records, total = parse_list(LIST_TEXT)
        assert total == 4
        assert [r["inn"] for r in records] == ["7712345678", "5036045205"]

    def test_fields_and_clone_detection(self):
        records, _ = parse_list(LIST_TEXT)
        pyramid, clone = records
        assert pyramid["cbr_id"] == 101
        assert pyramid["sign"] == 'Признаки "финансовой пирамиды"'
        assert pyramid["listed_at"] == datetime.date(2024, 5, 1)
        assert pyramid["closed"] is False and pyramid["is_clone"] is False
        assert clone["closed"] is True and clone["is_clone"] is True

    @pytest.mark.parametrize(
        "text",
        [
            "not json",
            "[]",
            '{"RC": null}',
            '{"RC": [{"Id": 1}]}',
            json.dumps({"RC": [{**LIST["RC"][0], "DT": "01.05.2024"}]}),
            json.dumps({"RC": [{**LIST["RC"][0], "INN": "12345"}]}),
            json.dumps({"RC": [{**LIST["RC"][0], "Closed": "no"}]}),
        ],
    )
    def test_drift_raises(self, text):
        with pytest.raises(CbrWarningError, match="схема ответа изменилась"):
            parse_list(text)

    def test_an_entry_missing_the_inn_key_is_drift_not_a_skipped_entry(self):
        entry = {k: v for k, v in LIST["RC"][0].items() if k != "INN"}
        with pytest.raises(CbrWarningError, match="нет ключа"):
            parse_list(json.dumps({"RC": [entry]}))


def _tables(make_session_factory):
    return make_session_factory([CbrWarningRecord.__table__, RegistryDump.__table__])


def _serve(patch_httpx_transport, text=LIST_TEXT):
    state = {"text": text}

    def handler(request):
        assert request.url.path == "/inside/warning-list/black-list-json"
        return httpx.Response(200, content=state["text"].encode())

    patch_httpx_transport(handler)
    return state


class TestRefreshAndLookup:
    def test_refresh_loads_and_lookup_matches_by_exact_inn(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        _serve(patch_httpx_transport)

        async def go():
            async with factory() as db:
                summary = await _locked(refresh_list, db)
                await db.commit()
                hit = await lookup_list(db, "7712345678")
                miss = await lookup_list(db, "7707083893")
                return summary, hit, miss

        summary, hit, miss = _run(go())
        assert summary["entries"] == 4 and summary["with_inn"] == 2
        assert [r["cbr_id"] for r in hit["records"]] == [101]
        assert hit["outdated"] is False
        assert miss["checked"] is True and miss["records"] == []

    def test_lookup_reports_the_clone_flag_and_closed_state(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        _serve(patch_httpx_transport)

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()
                return await lookup_list(db, "5036045205")

        (record,) = _run(go())["records"]
        assert record["is_clone"] is True and record["closed"] is True

    def test_refresh_replaces_rather_than_appends(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        _serve(patch_httpx_transport)

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()
                await _locked(refresh_list, db)
                await db.commit()
                return (
                    await db.execute(select(func.count()).select_from(CbrWarningRecord))
                ).scalar_one()

        assert _run(go()) == 2

    def test_a_list_that_lost_its_inns_is_rejected_and_old_data_kept(
        self, make_session_factory, patch_httpx_transport, monkeypatch
    ):
        factory = _tables(make_session_factory)
        portal = _serve(patch_httpx_transport)

        async def first():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()

        _run(first())
        # Every entry without an ИНН: the schema is intact but every lookup would be a
        # false "no match".
        stripped = {"RC": [{**e, "INN": ""} for e in LIST["RC"]]}
        portal["text"] = json.dumps(stripped)
        monkeypatch.setattr(svc, "SOURCE", dataclasses.replace(svc.SOURCE, min_matchable=2))

        async def second():
            async with factory() as db:
                with pytest.raises(CbrWarningError, match="из них 0 с ИНН"):
                    await _locked(refresh_list, db)
                await db.rollback()
                return (
                    await db.execute(select(func.count()).select_from(CbrWarningRecord))
                ).scalar_one()

        assert _run(second()) == 2

    def test_lookup_without_a_loaded_list_raises_never_reports_clean(self, make_session_factory):
        factory = _tables(make_session_factory)

        async def go():
            async with factory() as db:
                return await lookup_list(db, "7712345678")

        with pytest.raises(CbrWarningError, match="ещё не загружен"):
            _run(go())

    def test_http_errors_are_clean(self, make_session_factory, patch_httpx_transport):
        factory = _tables(make_session_factory)
        patch_httpx_transport(lambda request: httpx.Response(503, text="x"))

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)

        with pytest.raises(CbrWarningError, match="HTTP 503"):
            _run(go())

    def test_staleness_and_outdated_marker(self, make_session_factory, patch_httpx_transport):
        factory = _tables(make_session_factory)
        _serve(patch_httpx_transport)

        async def go():
            async with factory() as db:
                before = await is_stale(db, svc_module.SOURCE_KEY, svc_module.STALE_AFTER)
                await _locked(refresh_list, db)
                await db.commit()
                fresh = await is_stale(db, svc_module.SOURCE_KEY, svc_module.STALE_AFTER)
                meta = await db.get(RegistryDump, svc_module.SOURCE_KEY)
                meta.refreshed_at = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
                    days=20
                )
                await db.commit()
                return (
                    before,
                    fresh,
                    await is_stale(db, svc_module.SOURCE_KEY, svc_module.STALE_AFTER),
                    await lookup_list(db, "7712345678"),
                )

        before, fresh, later, lookup = _run(go())
        assert (before, fresh, later) == (True, False, True)
        assert lookup["outdated"] is True
