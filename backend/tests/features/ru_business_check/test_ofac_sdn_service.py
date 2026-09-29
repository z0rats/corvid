"""ofac_sdn_service against the SDN CSV shape captured live from OFAC on 2026-09-28: the
legacy 12-column header-less layout, `-0-` placeholders, `Tax ID No. <ИНН> (Russia)` inside the
remarks, a stray 0x1A at the end, and the treasury.gov -> sanctionslistservice -> signed
storage redirect chain. Names/numbers in the rows are synthetic."""

import asyncio
import dataclasses
import datetime

import httpx
import pytest
from sqlalchemy import func, select

from app.core.models.registry_dump import RegistryDump
from app.core.registry_dumps.common import is_stale, refresh_lock
from app.features.ru_business_check.models.ru_business_check_models import OfacSdnRecord
from app.features.ru_business_check.service import ofac_sdn_service as svc
from app.features.ru_business_check.service import ofac_sdn_service as svc_module
from app.features.ru_business_check.service.ofac_sdn_service import (
    OfacSdnError,
    is_allowed_redirect,
    lookup_list,
    parse_sdn,
    refresh_list,
)


def _row(num, name, kind="-0- ", program="RUSSIA-EO14024", remarks="-0- "):
    def q(v):
        return '"' + v.replace('"', '""') + '"'

    return f"{num},{q(name)},{kind},{q(program)},-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,-0- ,{q(remarks)}"


ENTITY = _row(
    16807,
    "OOO TRANSOIL",
    program="UKRAINE-EO13661] [RUSSIA-EO14024",
    remarks="Secondary sanctions risk: See Section 11.; Tax ID No. 7811139006 (Russia); "
    "Registration Number 1037825043200 (Russia).",
)
PERSON = _row(
    9001,
    "IVANOV, Ivan Ivanovich",
    kind="individual",
    remarks="DOB 01 Jan 1970; Tax ID No. 773407989940 (Russia).",
)
BANK_NO_INN = _row(17018, "PUBLIC JOINT STOCK COMPANY SBERBANK OF RUSSIA", remarks="SWIFT/BIC X")
FOREIGN = _row(36, "AEROCARIBBEAN AIRLINES", program="CUBA")
TWO_INNS = _row(
    77, "DOUBLE ID LLC", remarks="Tax ID No. 7711111111 (Russia); Tax ID No. 7722222222 (Russia)."
)
SAMPLE = "\r\n".join([ENTITY, PERSON, BANK_NO_INN, FOREIGN, TWO_INNS]) + "\r\n\x1a"


async def _locked(refresh, db):
    """Refreshes must run under the source's lock (enforced by `replace_dump`)."""
    async with refresh_lock(svc_module.SOURCE_KEY):
        return await refresh(db)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _relaxed_floors(monkeypatch):
    # The real floors are sized for the ~19k-entry live list; the fixture is tiny.
    monkeypatch.setattr(
        svc, "SOURCE", dataclasses.replace(svc.SOURCE, min_total=1, min_matchable=1)
    )


class TestParseSdn:
    def test_keeps_only_entries_with_a_russian_inn_and_counts_all(self):
        records, total = parse_sdn(SAMPLE)
        assert total == 5
        assert sorted(r["inn"] for r in records) == [
            "7711111111",
            "7722222222",
            "773407989940",
            "7811139006",
        ]

    def test_entity_fields(self):
        records, _ = parse_sdn(SAMPLE)
        transoil = next(r for r in records if r["inn"] == "7811139006")
        assert transoil["ent_num"] == 16807
        assert transoil["name"] == "OOO TRANSOIL"
        assert transoil["kind"] == "entity"
        assert transoil["programs"] == "UKRAINE-EO13661] [RUSSIA-EO14024"

    def test_an_individual_with_a_twelve_digit_inn_matches_too(self):
        records, _ = parse_sdn(SAMPLE)
        person = next(r for r in records if r["inn"] == "773407989940")
        assert person["kind"] == "individual"

    def test_the_trailing_eof_marker_and_blank_lines_are_ignored(self):
        records, total = parse_sdn(ENTITY + "\r\n\r\n\x1a")
        assert total == 1 and len(records) == 1

    def test_a_missing_program_placeholder_becomes_none(self):
        records, _ = parse_sdn(
            _row(5, "X", program="-0-", remarks="Tax ID No. 7700000000 (Russia)")
        )
        assert records[0]["programs"] is None

    @pytest.mark.parametrize("text", ["1,ONLY,THREE\n", ENTITY.replace("16807", "abc")])
    def test_drift_raises(self, text):
        with pytest.raises(OfacSdnError, match="схема ответа изменилась"):
            parse_sdn(text)


class TestRedirectPolicy:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.treasury.gov/ofac/downloads/sdn.csv",
            "https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/sdn.csv",
            "https://wc2h-sls-prod-public-published.s3.us-gov-west-1.amazonaws.com/Published/x/SDN.CSV?X-Amz=1",
        ],
    )
    def test_ofac_hosts_and_its_storage_are_allowed(self, url):
        assert is_allowed_redirect(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://www.treasury.gov/ofac/downloads/sdn.csv",
            "https://evil.example/sdn.csv",
            "https://www.treasury.gov.evil.example/sdn.csv",
            "https://bucket.s3.amazonaws.com/x",
            "https://x.s3.us-gov-west-1.amazonaws.com.evil.example/x",
            "file:///etc/passwd",
        ],
    )
    def test_anything_else_is_refused(self, url):
        assert not is_allowed_redirect(url)


def _tables(make_session_factory):
    return make_session_factory([OfacSdnRecord.__table__, RegistryDump.__table__])


def _serve_chain(
    patch_httpx_transport,
    body=SAMPLE,
    hop2="https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/sdn.csv",
):
    final = "https://bucket.s3.us-gov-west-1.amazonaws.com/Published/SDN.CSV?X-Amz-Signature=abc"
    state = {"body": body, "hits": []}

    def handler(request):
        url = str(request.url)
        state["hits"].append(request.url.host)
        if request.url.host == "www.treasury.gov":
            return httpx.Response(302, headers={"location": hop2})
        if request.url.host == "sanctionslistservice.ofac.treas.gov":
            return httpx.Response(302, headers={"location": final})
        assert url.startswith(final)
        return httpx.Response(200, content=state["body"].encode())

    patch_httpx_transport(handler)
    return state


class TestRefreshAndLookup:
    def test_follows_the_redirect_chain_and_loads_records(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        state = _serve_chain(patch_httpx_transport)

        async def go():
            async with factory() as db:
                summary = await _locked(refresh_list, db)
                await db.commit()
                return summary

        summary = _run(go())
        assert summary["entries"] == 5 and summary["with_inn"] == 4
        assert state["hits"] == [
            "www.treasury.gov",
            "sanctionslistservice.ofac.treas.gov",
            "bucket.s3.us-gov-west-1.amazonaws.com",
        ]

    def test_a_redirect_to_an_unexpected_host_is_refused(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        _serve_chain(patch_httpx_transport, hop2="https://evil.example/sdn.csv")

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)

        with pytest.raises(OfacSdnError, match="неожиданный адрес"):
            _run(go())

    def test_lookup_matches_entities_and_individuals_by_exact_inn(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        _serve_chain(patch_httpx_transport)

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()
                return (
                    await lookup_list(db, "7811139006"),
                    await lookup_list(db, "773407989940"),
                    await lookup_list(db, "7707083893"),
                )

        entity, person, miss = _run(go())
        assert [r["name"] for r in entity["records"]] == ["OOO TRANSOIL"]
        assert person["records"][0]["kind"] == "individual"
        assert miss["checked"] is True and miss["records"] == []

    def test_an_entry_without_an_inn_in_its_remarks_is_not_matchable(
        self, make_session_factory, patch_httpx_transport
    ):
        # The bank is on the list but carries no ИНН - the documented coverage gap: no
        # match must never be read as "not sanctioned".
        factory = _tables(make_session_factory)
        _serve_chain(patch_httpx_transport)

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()
                return (
                    await db.execute(
                        select(func.count())
                        .select_from(OfacSdnRecord)
                        .where(OfacSdnRecord.name.like("%SBERBANK%"))
                    )
                ).scalar_one()

        assert _run(go()) == 0

    def test_refresh_replaces_rather_than_appends(
        self, make_session_factory, patch_httpx_transport
    ):
        factory = _tables(make_session_factory)
        _serve_chain(patch_httpx_transport)

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()
                await _locked(refresh_list, db)
                await db.commit()
                return (
                    await db.execute(select(func.count()).select_from(OfacSdnRecord))
                ).scalar_one()

        assert _run(go()) == 4

    def test_a_list_that_lost_its_tax_ids_is_rejected_and_old_data_kept(
        self, make_session_factory, patch_httpx_transport, monkeypatch
    ):
        factory = _tables(make_session_factory)
        state = _serve_chain(patch_httpx_transport)

        async def first():
            async with factory() as db:
                await _locked(refresh_list, db)
                await db.commit()

        _run(first())
        state["body"] = "\r\n".join([FOREIGN, BANK_NO_INN]) + "\r\n\x1a"
        monkeypatch.setattr(svc, "SOURCE", dataclasses.replace(svc.SOURCE, min_matchable=2))

        async def second():
            async with factory() as db:
                with pytest.raises(OfacSdnError, match="из них 0 с ИНН"):
                    await _locked(refresh_list, db)
                await db.rollback()
                return (
                    await db.execute(select(func.count()).select_from(OfacSdnRecord))
                ).scalar_one()

        assert _run(second()) == 4

    def test_lookup_without_a_loaded_list_raises_never_reports_not_sanctioned(
        self, make_session_factory
    ):
        factory = _tables(make_session_factory)

        async def go():
            async with factory() as db:
                return await lookup_list(db, "7811139006")

        with pytest.raises(OfacSdnError, match="ещё не загружен"):
            _run(go())

    def test_http_errors_are_clean(self, make_session_factory, patch_httpx_transport):
        factory = _tables(make_session_factory)
        patch_httpx_transport(lambda request: httpx.Response(503, text="x"))

        async def go():
            async with factory() as db:
                await _locked(refresh_list, db)

        with pytest.raises(OfacSdnError, match="HTTP 503"):
            _run(go())

    def test_staleness_and_outdated_marker(self, make_session_factory, patch_httpx_transport):
        factory = _tables(make_session_factory)
        _serve_chain(patch_httpx_transport)

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
                    await lookup_list(db, "7811139006"),
                )

        before, fresh, later, lookup = _run(go())
        assert (before, fresh, later) == (True, False, True)
        assert lookup["outdated"] is True
