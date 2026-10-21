"""HTTP surface of the alerts inbox (`/api/alerts`) and the token-gated
`/ws/alerts` WebSocket that pushes new alerts to the AppBar bell."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from app.core.alerts.models.alerts_models import Alert
from app.core.alerts.routes import alerts_routes
from app.core.alerts.utils.alerts_websocket import ConnectionManager
from app.core.dependencies import get_db, get_read_db
from app.core.exceptions import register_exception_handlers
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from tests.conftest import run

TOKEN = "test-access-token"


@pytest.fixture
def ws_manager(monkeypatch):
    mgr = ConnectionManager()
    monkeypatch.setattr(alerts_routes, "manager", mgr)
    monkeypatch.setattr("app.core.alerts.service.alerts_service.manager", mgr)
    return mgr


@pytest.fixture
def client(make_session_factory, monkeypatch, ws_manager):
    session_factory = make_session_factory([Alert.__table__, TelegramSettings.__table__])

    async def _get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as db:
            yield db
            await db.commit()

    monkeypatch.setattr(alerts_routes, "get_access_token", lambda: TOKEN)
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(alerts_routes.router)
    app.include_router(alerts_routes.ws_router)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_read_db] = _get_db
    return TestClient(app)


def _create(client, module="scanner", title="Done", message="Scan finished"):
    r = client.post("/api/alerts", json={"module": module, "title": title, "message": message})
    assert r.status_code == 201
    return r.json()


class TestCrud:
    def test_create_list_get(self, client):
        a = _create(client, title="first")
        b = _create(client, title="second")
        assert a["read"] is False

        listed = client.get("/api/alerts").json()
        assert {x["id"] for x in listed} == {a["id"], b["id"]}
        assert client.get(f"/api/alerts/{a['id']}").json()["title"] == "first"

    def test_pagination_and_module_filter(self, client):
        for i in range(3):
            _create(client, module="newsfeed", title=f"n{i}")
        _create(client, module="amass")

        assert len(client.get("/api/alerts", params={"limit": 2}).json()) == 2
        assert len(client.get("/api/alerts", params={"skip": 3}).json()) == 1
        mod = client.get("/api/alerts/module/newsfeed").json()
        assert len(mod) == 3
        assert {x["module"] for x in mod} == {"newsfeed"}

    def test_mark_read_unread_sets_and_clears_read_timestamp(self, client):
        a = _create(client)
        r = client.patch(f"/api/alerts/{a['id']}", json={"read": True}).json()
        assert r["read"] is True
        assert r["timestamp_read"]
        assert client.get("/api/alerts/count/unread").json() == {"unread_count": 0}

        r = client.patch(f"/api/alerts/{a['id']}", json={"read": False}).json()
        assert r["read"] is False
        assert "timestamp_read" not in r  # cleared -> excluded as None
        assert client.get("/api/alerts/count/unread").json() == {"unread_count": 1}

    def test_bulk_mark_read_counts_only_unread(self, client):
        a = _create(client)
        _create(client)
        _create(client)
        client.patch(f"/api/alerts/{a['id']}", json={"read": True})
        r = client.patch("/api/alerts").json()
        assert r["count"] == 2
        assert client.get("/api/alerts/count/unread").json()["unread_count"] == 0

    def test_delete_single_and_all(self, client):
        a = _create(client)
        _create(client)
        _create(client)
        assert client.delete(f"/api/alerts/{a['id']}").status_code == 204
        assert client.get(f"/api/alerts/{a['id']}").status_code == 404
        assert client.delete("/api/alerts").json()["count"] == 2
        assert client.get("/api/alerts").json() == []

    @pytest.mark.parametrize(
        ("method", "kwargs"),
        [("get", {}), ("patch", {"json": {"read": True}}), ("delete", {})],
    )
    def test_missing_alert_404(self, client, method, kwargs):
        r = getattr(client, method)("/api/alerts/999", **kwargs)
        assert r.status_code == 404
        assert r.json()["error_code"] == "ALERT_NOT_FOUND"

    def test_non_positive_id_rejected(self, client):
        assert client.get("/api/alerts/0").status_code == 422


class TestWebSocket:
    @pytest.mark.parametrize("token", ["", "wrong", TOKEN + "x"])
    def test_rejects_bad_token(self, client, ws_manager, token):
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(f"/ws/alerts?token={token}") as ws:
                ws.receive_text()
        assert exc.value.code == 4001
        assert ws_manager.active_connections == []

    def test_valid_token_receives_new_alert_broadcast(self, client, ws_manager):
        with client.websocket_connect(f"/ws/alerts?token={TOKEN}") as ws:
            assert len(ws_manager.active_connections) == 1
            created = _create(client, title="pushed")
            msg = ws.receive_json()
            assert msg["id"] == created["id"]
            assert msg["title"] == "pushed"
            assert msg["read"] is False
        assert ws_manager.active_connections == []


class TestConnectionManager:
    def test_broadcast_drops_dead_connections(self):
        class Conn:
            def __init__(self, fail):
                self.fail, self.sent = fail, []

            async def send_json(self, msg):
                if self.fail:
                    raise RuntimeError("closed")
                self.sent.append(msg)

        mgr = ConnectionManager()
        good, bad = Conn(False), Conn(True)
        mgr.active_connections = [good, bad]
        run(mgr.broadcast({"x": 1}))
        assert good.sent == [{"x": 1}]
        assert mgr.active_connections == [good]

    def test_disconnect_unknown_is_noop_and_empty_broadcast_ok(self):
        mgr = ConnectionManager()
        mgr.disconnect(object())
        run(mgr.broadcast({"x": 1}))
