"""`ScanFeature` + `add_run_routes` - the run-history interface every scan feature
mounts (cancel/list/get/delete). Exercised once here against a real table; each
feature's own route tests only need what's specific to it."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.scans.crud import ScanColumns
from app.core.scans.feature import ScanFeature
from app.core.scans.routes import add_run_routes
from app.core.scans.run import ScanRun
from app.features.amass.models.amass_models import AmassSearch
from app.features.amass.schemas.amass_schemas import SearchDetail, SearchSummary

FEATURE = ScanFeature(
    name="test_feature",
    model=AmassSearch,
    columns=ScanColumns(error_column="error", completed_at_column=None),
    order_by=AmassSearch.searched_at,
)


class FakeCancellable:
    def __init__(self):
        self.cancelled = False

    async def cancel(self):
        self.cancelled = True


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([AmassSearch.__table__])


def _seed(session_factory, *domains, status="completed"):
    async def _insert():
        async with session_factory() as db:
            rows = [AmassSearch(domain=d, status=status) for d in domains]
            db.add_all(rows)
            await db.commit()
            return [r.id for r in rows]

    return asyncio.run(_insert())


def _client(session_factory, **route_kwargs):
    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    router = APIRouter(prefix="/api/test")
    add_run_routes(
        router,
        FEATURE,
        display_name="test",
        summary_schema=SearchSummary,
        detail_schema=SearchDetail,
        not_found_code="TEST_NOT_FOUND",
        **route_kwargs,
    )
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


class TestHistoryRoutes:
    def test_lists_newest_first_with_paging(self, session_factory):
        _seed(session_factory, "a.com", "b.com", "c.com")
        client = _client(session_factory)

        body = client.get("/api/test/history", params={"skip": 0, "limit": 2}).json()

        assert len(body) == 2
        assert set(body[0]) == set(SearchSummary.model_fields)

    def test_get_and_delete(self, session_factory):
        (search_id,) = _seed(session_factory, "a.com")
        client = _client(session_factory)

        assert client.get(f"/api/test/history/{search_id}").json()["domain"] == "a.com"
        assert client.delete(f"/api/test/history/{search_id}").status_code == 204
        missing = client.get(f"/api/test/history/{search_id}")
        assert missing.status_code == 404
        assert missing.json()["error_code"] == "TEST_NOT_FOUND"
        assert client.delete(f"/api/test/history/{search_id}").status_code == 404

    def test_custom_base_detail_and_after_delete(self, session_factory):
        (search_id,) = _seed(session_factory, "a.com")
        deleted = []

        def to_detail(run):
            return SearchDetail.model_validate(run).model_copy(update={"error": "decorated"})

        client = _client(
            session_factory, base="runs", to_detail=to_detail, after_delete=deleted.append
        )

        assert client.get(f"/api/test/runs/{search_id}").json()["error"] == "decorated"
        client.delete(f"/api/test/runs/{search_id}")
        assert deleted == [search_id]


class TestCancelRoute:
    def test_404_with_not_running_code_when_nothing_runs(self, session_factory):
        client = _client(session_factory, not_running_code="TEST_NOT_RUNNING")

        response = client.post("/api/test/history/424242/cancel")

        assert response.status_code == 404
        assert response.json()["error_code"] == "TEST_NOT_RUNNING"

    def test_cancels_the_run_registered_for_this_table(self, session_factory):
        cancellable = FakeCancellable()
        ScanRun._registry[(AmassSearch, 7)] = cancellable
        try:
            response = _client(session_factory).post("/api/test/history/7/cancel")
        finally:
            ScanRun._registry.pop((AmassSearch, 7), None)

        assert response.status_code == 202
        assert cancellable.cancelled is True


class TestInterruptRunning:
    def test_marks_only_running_rows_failed(self, session_factory):
        running_id, done_id = (
            _seed(session_factory, "a.com", status="running")[0],
            _seed(session_factory, "b.com")[0],
        )

        async def _scenario():
            async with session_factory() as db:
                count = await FEATURE.interrupt_running(db)
                await db.commit()
            async with session_factory() as db:
                return (
                    count,
                    await db.get(AmassSearch, running_id),
                    await db.get(AmassSearch, done_id),
                )

        count, running, done = asyncio.run(_scenario())
        assert count == 1
        assert (running.status, running.error) == ("failed", "Interrupted by server restart")
        assert done.status == "completed"
