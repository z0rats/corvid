"""verify_access_token is the single dependency gating almost every /api/*
route (see access_control.py's module docstring) - these tests exercise it
through a real HTTP request/response cycle via TestClient, rather than
calling the function directly with a hand-built Header value, so they cover
the actual contract a client (or attacker) hits."""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.security import access_control
from app.core.security.access_control import verify_access_token

KNOWN_TOKEN = "test-token-abc123"


@pytest.fixture
def client(monkeypatch):
    """A minimal app with one route behind the real dependency, and a fixed,
    known token (bypassing the file-backed lru_cache'd token source, which is
    an I/O edge orthogonal to the verification logic under test)."""
    monkeypatch.setattr(access_control, "get_access_token", lambda: KNOWN_TOKEN)

    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_access_token)])
    async def protected():
        return {"ok": True}

    return TestClient(app)


def test_valid_bearer_token_is_accepted(client):
    response = client.get("/protected", headers={"Authorization": f"Bearer {KNOWN_TOKEN}"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_missing_authorization_header_is_rejected(client):
    response = client.get("/protected")

    assert response.status_code == 401


def test_wrong_token_is_rejected(client):
    response = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401


def test_missing_bearer_prefix_is_rejected(client):
    response = client.get("/protected", headers={"Authorization": KNOWN_TOKEN})

    assert response.status_code == 401


def test_bearer_prefix_is_case_insensitive(client):
    response = client.get("/protected", headers={"Authorization": f"bearer {KNOWN_TOKEN}"})

    assert response.status_code == 200


def test_empty_bearer_token_is_rejected(client):
    response = client.get("/protected", headers={"Authorization": "Bearer "})

    assert response.status_code == 401


def test_token_as_query_param_is_not_accepted(client):
    # verify_access_token only reads the Authorization header; a token
    # leaked into a query string/URL (logs, browser history, referrers)
    # must not work as a bypass.
    response = client.get(f"/protected?token={KNOWN_TOKEN}")

    assert response.status_code == 401


def test_missing_and_wrong_token_return_the_same_error_detail(client):
    # Intentional: the 401 message doesn't distinguish "no header" from
    # "wrong token" so it can't be used as an oracle to probe for a partially
    # correct token or to distinguish an unset vs. misconfigured deployment.
    missing = client.get("/protected")
    wrong = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]
