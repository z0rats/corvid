from types import SimpleNamespace

from app.features.username_search.service.username_search_service import _extract_found_sites


def _status(found=True, ids_data=None):
    return SimpleNamespace(is_found=lambda: found, ids_data=ids_data)


def test_extracts_discovered_usernames_links_and_names():
    results = {
        "GitHub": {
            "status": _status(ids_data={"fullname": " John Smith "}),
            "url_user": "https://github.com/jsmith",
            "http_status": 200,
            "ids_usernames": {"jsmith": "username", "JSmith_alt": "username", "12345": "vk_id"},
            "ids_links": ["https://jsmith.dev"],
        }
    }

    (site,) = _extract_found_sites(results, "jsmith")

    assert site["extra"] == {
        "discovered_usernames": [
            {"value": "JSmith_alt", "type": "username"},
            {"value": "12345", "type": "vk_id"},
        ],
        "discovered_links": ["https://jsmith.dev"],
        "discovered_names": ["John Smith"],
    }


def test_extra_is_none_when_nothing_discovered_and_unfound_sites_skipped():
    results = {
        "Plain": {"status": _status(), "url_user": "https://x.test/u", "http_status": 200},
        "Missing": {"status": _status(found=False), "url_user": "https://y.test/u"},
    }

    sites = _extract_found_sites(results, "u")

    assert [s["site_name"] for s in sites] == ["Plain"]
    assert sites[0]["extra"] is None


def test_extracts_published_emails_from_profile_fields_and_drops_relays():
    results = {
        "GitHub": {
            "status": _status(
                ids_data={
                    "email": "Dev@Acme.dev",
                    "emails": ["noreply@acme.dev", "second@acme.dev"],
                    "bio": "mail me at not-a-field@acme.dev",
                }
            ),
            "url_user": "https://github.com/jsmith",
            "http_status": 200,
        }
    }

    (site,) = _extract_found_sites(results, "jsmith")

    assert site["extra"] == {"discovered_emails": ["dev@acme.dev", "second@acme.dev"]}


class TestAnnotateAgainstParent:
    """`_annotate_against_parent` loads the followed run and rates the new hits against it."""

    @staticmethod
    def _scenario(make_session_factory, monkeypatch, parent_exists):
        import contextlib

        from app.features.username_search.crud.username_search_crud import add_site_results
        from app.features.username_search.models.username_search_models import (
            MaigretSearch,
            MaigretSiteResult,
        )
        from app.features.username_search.service import username_search_service as svc
        from tests.conftest import run

        factory = make_session_factory([MaigretSearch.__table__, MaigretSiteResult.__table__])

        @contextlib.asynccontextmanager
        async def fake_managed_session():
            async with factory() as db:
                yield db

        monkeypatch.setattr(svc, "managed_session", fake_managed_session)
        rows = [
            {"site_name": "Reddit", "url_user": "u", "extra": {"discovered_names": ["Maria"]}},
            {"site_name": "Twitter", "url_user": "u", "extra": None},
        ]

        async def go():
            if parent_exists:
                async with factory() as db:
                    db.add(MaigretSearch(username="jsmith", status="completed"))
                    await db.flush()
                    await add_site_results(
                        db,
                        1,
                        [
                            {
                                "site_name": "GitHub",
                                "url_user": "u",
                                "extra": {
                                    "discovered_names": ["John Smith"],
                                    "discovered_links": ["https://twitter.com/jsmith_dev"],
                                },
                            }
                        ],
                    )
                    await db.commit()
            await svc._annotate_against_parent(rows, "jsmith_dev", 1)

        run(go())
        return rows

    def test_rates_hits_against_the_parents_findings(self, make_session_factory, monkeypatch):
        rows = self._scenario(make_session_factory, monkeypatch, parent_exists=True)
        assert [r["extra"]["confidence"] for r in rows] == ["conflicting", "confirmed"]

    def test_a_deleted_parent_leaves_hits_unrated(self, make_session_factory, monkeypatch):
        rows = self._scenario(make_session_factory, monkeypatch, parent_exists=False)
        assert "confidence" not in (rows[0]["extra"] or {})
        assert rows[1]["extra"] is None


def test_a_failing_parent_lookup_leaves_hits_unrated_instead_of_raising(monkeypatch):
    import contextlib

    from app.features.username_search.service import username_search_service as svc
    from tests.conftest import run

    @contextlib.asynccontextmanager
    async def broken_session():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr(svc, "managed_session", broken_session)
    rows = [{"site_name": "Reddit", "url_user": "u", "extra": None}]

    run(svc._annotate_against_parent(rows, "x", 1))

    assert rows[0]["extra"] is None


class TestRunScan:
    """`run_scan` driven through stubbed Maigret/persistence, outcome captured from `run_work`."""

    @staticmethod
    def _verdict(found, value):
        return SimpleNamespace(
            is_found=lambda: found, ids_data=None, status=SimpleNamespace(value=value)
        )

    def _scenario(self, monkeypatch, *, site_names, cancel=False, parent_search_id=None):
        import asyncio
        import contextlib

        from app.core.scans.run import ScanCancelled
        from app.features.username_search.service import username_search_service as svc

        calls: list[str] = []
        results = {
            "GitHub": {"status": self._verdict(True, "Claimed"), "url_user": "https://g/u"},
            "GitLab": {"status": self._verdict(False, "Unknown")},
        }

        @contextlib.asynccontextmanager
        async def fake_session():
            yield None

        async def fake_config(_db):
            return SimpleNamespace(
                timeout_seconds=1, max_concurrency=1, top_sites_count=10, proxy_url=None
            )

        async def fake_maigret(**kwargs):
            kwargs["output_container"].update(results)
            if cancel:
                raise asyncio.CancelledError
            return results

        async def fake_annotate(found_sites, username, parent_id):
            calls.append("annotate")

        outcome = {}

        async def fake_execute(run_work, on_event, **kwargs):
            try:
                outcome["value"] = await run_work(1)
            except ScanCancelled as exc:
                outcome["value"] = exc.outcome

        monkeypatch.setattr(svc, "managed_session", fake_session)
        monkeypatch.setattr(svc, "get_username_search_config", fake_config)
        monkeypatch.setattr(svc, "get_site_dict", lambda *a, **k: dict.fromkeys(results))
        monkeypatch.setattr(svc, "run_maigret_checks", fake_maigret)
        monkeypatch.setattr(svc, "save_scan_results", lambda *_: calls.append("save"))
        monkeypatch.setattr(svc, "_annotate_against_parent", fake_annotate)
        monkeypatch.setattr(svc, "USERNAME_SEARCH_SCANS", SimpleNamespace(execute=fake_execute))

        asyncio.run(
            svc.run_scan(
                "u",
                asyncio.Queue(),
                site_names=site_names,
                parent_search_id=parent_search_id,
            )
        )
        return outcome["value"], calls

    def test_a_site_check_keeps_every_verdict_so_a_blocked_site_is_not_not_found(self, monkeypatch):
        outcome, _ = self._scenario(monkeypatch, site_names=["GitHub", "GitLab"])
        assert outcome.db_only_fields == {
            "site_statuses": {"GitHub": "claimed", "GitLab": "unknown"}
        }

    def test_a_full_scan_stores_no_verdicts(self, monkeypatch):
        outcome, _ = self._scenario(monkeypatch, site_names=None)
        assert outcome.db_only_fields == {}

    def test_cancellation_saves_the_report_before_the_parent_lookup(self, monkeypatch):
        outcome, calls = self._scenario(
            monkeypatch, site_names=["GitHub", "GitLab"], cancel=True, parent_search_id=3
        )
        assert calls == ["save", "annotate"]
        assert outcome.db_only_fields["site_statuses"]["GitLab"] == "unknown"
