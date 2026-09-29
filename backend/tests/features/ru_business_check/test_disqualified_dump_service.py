"""disqualified_dump_service against the dataset shape captured live from data.nalog.ru on
2026-09-28 (meta.csv layout, G1..G14 header, DD.MM.YYYY dates, org ИНН on ~36% of rows).
Names and numbers in the rows are synthetic."""

import asyncio
import datetime

import httpx
import pytest

from app.core.models.registry_dump import RegistryDump
from app.core.registry_dumps.common import is_stale, refresh_lock
from app.features.ru_business_check.models.ru_business_check_models import DisqualifiedRecord
from app.features.ru_business_check.service import disqualified_dump_service as svc_module
from app.features.ru_business_check.service.disqualified_dump_service import (
    PORTAL,
    DisqualifiedDumpError,
    lookup_dump,
    normalize_name,
    parse_dump,
    parse_meta,
    refresh_dump,
)

META_CSV = f"""property,value
standardversion,http://opendata.gosmonitor.ru/standard/3.0
identifier,7707329152-registerdisqualified
valid,20261004
data-20200315-structure-24062015.csv,{PORTAL}/data-20200315-structure-24062015.csv
data-20260913-structure-20150624.csv,{PORTAL}/data-20260913-structure-20150624.csv
data-20260920-structure-20150624.csv,{PORTAL}/data-20260920-structure-20150624.csv
"""

HEADER = ",".join(f"G{i}" for i in range(1, 15))
COMPANY_INN = "7712345678"
TODAY = datetime.date(2026, 9, 28)


def _row(
    number="100000000001",
    name="ИВАНОВ ИВАН ИВАНОВИЧ",
    org='ООО "РОМАШКА"',
    inn=COMPANY_INN,
    start="28.11.2025",
    end="27.11.2027",
):
    return (
        f'{number},{name},19.03.1980,"Г. ТУЛА","{org.replace(chr(34), chr(34) * 2)}",{inn},'
        f"РУКОВОДИТЕЛЬ,Ч.5 СТ. 14.25 КОАП РФ,МИФНС РОССИИ № 46,КУРАХТАНОВ А В,МИРОВОЙ СУДЬЯ,"
        f"2 г 0 м 0 д,{start},{end}"
    )


def _csv(*rows):
    return "\n".join([HEADER, *rows]) + "\n"


async def _locked(refresh, db):
    """Refreshes must run under the source's lock (enforced by `replace_dump`)."""
    async with refresh_lock(svc_module.SOURCE_KEY):
        return await refresh(db)


def _run(coro):
    return asyncio.run(coro)


class TestParseMeta:
    def test_picks_the_newest_data_version_and_its_dates(self):
        url, dump_date, valid_until = parse_meta(META_CSV)
        assert url.endswith("data-20260920-structure-20150624.csv")
        assert dump_date == datetime.date(2026, 9, 20)
        assert valid_until == datetime.date(2026, 10, 4)

    def test_no_data_rows_is_drift(self):
        with pytest.raises(DisqualifiedDumpError, match="нет ссылок на данные"):
            parse_meta("property,value\nvalid,20261004\n")

    def test_a_url_outside_the_dataset_is_refused(self):
        meta = "data-20260920-x.csv,https://evil.example/data-20260920-x.csv\n"
        with pytest.raises(DisqualifiedDumpError, match="вне набора"):
            parse_meta(meta)

    def test_missing_valid_is_none(self):
        text = f"data-20260920-x.csv,{PORTAL}/data-20260920-x.csv\n"
        assert parse_meta(text)[2] is None


class TestParseDump:
    def test_row_columns_and_normalization(self):
        (rec,) = parse_dump(_csv(_row(name="Иванов  Иван Иванович")))
        assert rec["record_number"] == "100000000001"
        assert rec["full_name"] == "ИВАНОВ ИВАН ИВАНОВИЧ"
        assert rec["org_name"] == 'ООО "РОМАШКА"'
        assert rec["org_inn"] == COMPANY_INN
        assert rec["position"] == "РУКОВОДИТЕЛЬ"
        assert rec["term"] == "2 г 0 м 0 д"
        assert rec["start_date"] == datetime.date(2025, 11, 28)
        assert rec["end_date"] == datetime.date(2027, 11, 27)

    def test_birth_data_and_judge_are_not_kept(self):
        (rec,) = parse_dump(_csv(_row()))
        assert not ({"birth_date", "birth_place", "judge", "protocol_body"} & set(rec))
        assert "1980" not in str(rec.values()) and "ТУЛА" not in str(rec.values())

    def test_a_missing_or_malformed_org_inn_is_none(self):
        recs = parse_dump(_csv(_row(inn=""), _row(number="2", inn="123")))
        assert [r["org_inn"] for r in recs] == [None, None]

    def test_yo_folding_matches_between_stored_and_searched_names(self):
        assert normalize_name("Фёдоров Пётр") == normalize_name("ФЕДОРОВ ПЕТР")

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "G1,G2\n1,2\n",
            _csv("only,three,columns"),
            _csv(_row(name="")),
            _csv(_row(start="2025-11-28")),
            _csv(_row(start="31.02.2025")),
        ],
    )
    def test_drift_raises(self, text):
        with pytest.raises(DisqualifiedDumpError, match="схема выгрузки изменилась"):
            parse_dump(text)


def _tables(make_session_factory):
    return make_session_factory([DisqualifiedRecord.__table__, RegistryDump.__table__])


def _mock_portal(patch_httpx_transport, csv_text, meta=META_CSV):
    """Serve the portal from a mutable state dict (`patch_httpx_transport` can only be
    applied once per test) - change `state["csv"]` to publish a new dataset version."""
    state = {"csv": csv_text}

    def handler(request):
        if request.url.path.endswith("/meta.csv"):
            return httpx.Response(200, text=meta)
        return httpx.Response(200, content=state["csv"].encode("utf-8-sig"))

    patch_httpx_transport(handler)
    return state


class TestRefresh:
    def test_loads_records_and_provenance(self, make_session_factory, patch_httpx_transport):
        session_factory = _tables(make_session_factory)
        _mock_portal(patch_httpx_transport, _csv(_row(), _row(number="2", inn="")))

        async def go():
            async with session_factory() as db:
                summary = await _locked(refresh_dump, db)
                await db.commit()
                meta = await db.get(RegistryDump, svc_module.SOURCE_KEY)
                return summary, meta

        summary, meta = _run(go())
        assert summary["rows"] == 2
        assert meta.row_count == 2
        assert meta.dump_date == datetime.date(2026, 9, 20)
        assert meta.valid_until == datetime.date(2026, 10, 4)

    def test_a_second_refresh_replaces_rather_than_appends(
        self, make_session_factory, patch_httpx_transport
    ):
        session_factory = _tables(make_session_factory)
        _mock_portal(patch_httpx_transport, _csv(_row(), _row(number="2")))

        from sqlalchemy import func, select

        async def count():
            async with session_factory() as db:
                await _locked(refresh_dump, db)
                await db.commit()
                await _locked(refresh_dump, db)
                await db.commit()
                return (
                    await db.execute(select(func.count()).select_from(DisqualifiedRecord))
                ).scalar_one()

        assert _run(count()) == 2

    def test_a_suspiciously_small_new_version_is_rejected_and_old_data_kept(
        self, make_session_factory, patch_httpx_transport
    ):
        session_factory = _tables(make_session_factory)
        from sqlalchemy import func, select

        portal = _mock_portal(
            patch_httpx_transport, _csv(*[_row(number=str(i)) for i in range(10)])
        )

        async def first():
            async with session_factory() as db:
                await _locked(refresh_dump, db)
                await db.commit()

        _run(first())

        portal["csv"] = _csv(_row(number="1"))

        async def second():
            async with session_factory() as db:
                with pytest.raises(DisqualifiedDumpError, match="записей вместо"):
                    await _locked(refresh_dump, db)
                await db.rollback()
                return (
                    await db.execute(select(func.count()).select_from(DisqualifiedRecord))
                ).scalar_one()

        assert _run(second()) == 10

    def test_download_errors_are_clean(self, make_session_factory, patch_httpx_transport):
        session_factory = _tables(make_session_factory)
        patch_httpx_transport(lambda request: httpx.Response(503, text="x"))

        async def go():
            async with session_factory() as db:
                await _locked(refresh_dump, db)

        with pytest.raises(DisqualifiedDumpError, match="HTTP 503"):
            _run(go())


class TestLookup:
    def _loaded(self, make_session_factory, patch_httpx_transport, *rows):
        session_factory = _tables(make_session_factory)
        _mock_portal(patch_httpx_transport, _csv(*rows))

        async def load():
            async with session_factory() as db:
                await _locked(refresh_dump, db)
                await db.commit()

        _run(load())
        return session_factory

    def _lookup(self, session_factory, name="ИВАНОВ ИВАН ИВАНОВИЧ", inn=COMPANY_INN):
        async def go():
            async with session_factory() as db:
                return await lookup_dump(db, inn, name, today=TODAY)

        return _run(go())

    def test_same_person_same_company_in_force_is_confirmed(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = self._loaded(make_session_factory, patch_httpx_transport, _row())
        result = self._lookup(factory)
        assert result["director_confirmed"] is True
        assert result["director_records"][0]["same_company"] is True
        assert result["dump_date"] == "2026-09-20"

    def test_the_confirming_record_is_listed_first_even_among_many_namesakes(
        self, make_session_factory, patch_httpx_transport, monkeypatch
    ):
        from app.features.ru_business_check.service import disqualified_dump_service

        monkeypatch.setattr(disqualified_dump_service, "MAX_LISTED_RECORDS", 2)
        namesakes = [_row(number=str(i), inn="5036045205") for i in range(5)]
        factory = self._loaded(
            make_session_factory, patch_httpx_transport, *namesakes, _row(number="999")
        )
        result = self._lookup(factory)
        assert result["director_confirmed"] is True
        assert result["director_records"][0]["record_number"] == "999"
        assert len(result["director_records"]) == 2

    def test_a_namesake_of_another_company_is_not_confirmed(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = self._loaded(make_session_factory, patch_httpx_transport, _row(inn="5036045205"))
        result = self._lookup(factory)
        assert result["director_confirmed"] is False
        assert len(result["director_records"]) == 1  # still listed for manual review
        assert result["company_records"] == []

    def test_an_expired_record_of_the_same_person_and_company_is_not_confirmed(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = self._loaded(
            make_session_factory,
            patch_httpx_transport,
            _row(start="01.01.2020", end="01.01.2022"),
        )
        result = self._lookup(factory)
        assert result["director_confirmed"] is False
        assert result["director_records"][0]["active"] is False

    def test_other_officers_of_the_company_are_listed_by_inn(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = self._loaded(
            make_session_factory,
            patch_httpx_transport,
            _row(number="7", name="ПЕТРОВ ПЕТР ПЕТРОВИЧ"),
        )
        result = self._lookup(factory)
        assert result["director_confirmed"] is False
        assert [r["record_number"] for r in result["company_records"]] == ["7"]

    def test_yo_variants_of_the_directors_name_still_match(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = self._loaded(
            make_session_factory, patch_httpx_transport, _row(name="ФЁДОРОВ ПЁТР ИВАНОВИЧ")
        )
        result = self._lookup(factory, name="Федоров Петр Иванович")
        assert result["director_confirmed"] is True

    def test_no_director_name_still_lists_company_records(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = self._loaded(make_session_factory, patch_httpx_transport, _row())
        result = self._lookup(factory, name=None)
        assert result["director_records"] == []
        assert len(result["company_records"]) == 1

    def test_lookup_without_a_loaded_dump_raises_never_reports_clean(self, make_session_factory):
        session_factory = _tables(make_session_factory)

        async def go():
            async with session_factory() as db:
                return await lookup_dump(db, COMPANY_INN, "ИВАНОВ ИВАН ИВАНОВИЧ")

        with pytest.raises(DisqualifiedDumpError, match="ещё не загружена"):
            _run(go())


class TestStaleness:
    def test_missing_dump_is_stale_then_fresh_after_a_refresh(
        self, make_session_factory, patch_httpx_transport
    ):
        session_factory = _tables(make_session_factory)
        _mock_portal(patch_httpx_transport, _csv(_row()))

        async def go():
            async with session_factory() as db:
                before = await is_stale(db, svc_module.SOURCE_KEY, svc_module.STALE_AFTER)
                await _locked(refresh_dump, db)
                await db.commit()
                fresh = await is_stale(db, svc_module.SOURCE_KEY, svc_module.STALE_AFTER)
                meta = await db.get(RegistryDump, svc_module.SOURCE_KEY)
                meta.refreshed_at = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=8)
                await db.commit()
                return (
                    before,
                    fresh,
                    await is_stale(db, svc_module.SOURCE_KEY, svc_module.STALE_AFTER),
                )

        assert _run(go()) == (True, False, True)
