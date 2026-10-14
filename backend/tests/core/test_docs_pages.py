"""/docs and /redoc are public HTML shells (a browser can't send the bearer header on a plain
navigation); the API description they load, /openapi.json, stays behind the access token."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import docs_pages
from app.core.security import access_control

FRONTEND_TOKEN_MODULE = (
    Path(__file__).resolve().parents[3] / "frontend/src/core/utils/accessToken.js"
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(docs_pages.settings, "environment", "development")
    monkeypatch.setattr(access_control, "get_access_token", lambda: "secret-token")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, title="Corvid")
    docs_pages.add_docs_routes(app)
    return TestClient(app)


@pytest.mark.parametrize("path", ["/docs", "/redoc"])
def test_shells_load_without_a_token_and_send_the_stored_one(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert f'localStorage.getItem("{docs_pages.TOKEN_STORAGE_KEY}")' in response.text
    assert '"Bearer " + token' in response.text
    assert "secret-token" not in response.text


def test_openapi_json_still_requires_the_token(client):
    assert client.get("/openapi.json").status_code == 401

    response = client.get("/openapi.json", headers={"Authorization": "Bearer secret-token"})
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Corvid"


def test_not_mounted_in_production(monkeypatch):
    monkeypatch.setattr(docs_pages.settings, "environment", "production")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    docs_pages.add_docs_routes(app)

    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_title_is_html_escaped():
    assert "<script>x" not in docs_pages.swagger_ui_page("<script>x").body.decode()


def test_storage_key_matches_the_spa():
    assert f"'{docs_pages.TOKEN_STORAGE_KEY}'" in FRONTEND_TOKEN_MODULE.read_text()
