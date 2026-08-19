"""Encryption-touching tests monkeypatch secrets_crypto._get_fernet to a fixed
in-memory key, same pattern as test_secrets_crypto.py, so they never touch
this developer's real <data_dir>/.encryption_key file."""

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select, text

from app.core.security import secrets_crypto
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey
from tests.conftest import run as _run


@pytest.fixture
def session_factory(make_session_factory):
    return make_session_factory([Apikey.__table__])


@pytest.fixture(autouse=True)
def fixed_fernet(monkeypatch):
    fixed = Fernet(Fernet.generate_key())
    monkeypatch.setattr(secrets_crypto, "_get_fernet", lambda: fixed)
    return fixed


# --- @validates('name') ------------------------------------------------


def test_name_is_stripped_and_lowercased():
    apikey = Apikey(name="  VirusTotal  ", key="k")
    assert apikey.name == "virustotal"


def test_empty_name_is_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        Apikey(name="   ", key="k")


def test_overly_long_name_is_rejected():
    with pytest.raises(ValueError, match="cannot exceed 100 characters"):
        Apikey(name="a" * 101, key="k")


# --- @validates('key') ---------------------------------------------------


def test_key_is_stripped():
    apikey = Apikey(name="vt", key="  abc123  ")
    assert apikey.key == "abc123"


def test_none_key_becomes_empty_string():
    apikey = Apikey(name="vt", key=None)
    assert apikey.key == ""


def test_overly_long_key_is_rejected():
    with pytest.raises(ValueError, match="cannot exceed 500 characters"):
        Apikey(name="vt", key="a" * 501)


# --- is_configured / is_usable ------------------------------------------


def test_is_configured_false_for_empty_key():
    assert Apikey(name="vt", key="").is_configured() is False


def test_is_configured_true_for_non_empty_key():
    assert Apikey(name="vt", key="abc").is_configured() is True


def test_is_usable_requires_both_configured_and_active():
    assert Apikey(name="vt", key="abc", is_active=False).is_usable() is False
    assert Apikey(name="vt", key="", is_active=True).is_usable() is False
    assert Apikey(name="vt", key="abc", is_active=True).is_usable() is True


# --- __repr__ / __str__ ----------------------------------------------------


def test_repr_reflects_status_and_configuration():
    apikey = Apikey(name="vt", key="abc", is_active=True)
    assert "active" in repr(apikey)
    assert "configured" in repr(apikey)


def test_str_reflects_active_status():
    assert "active" in str(Apikey(name="vt", key="abc", is_active=True))
    assert "inactive" in str(Apikey(name="vt", key="abc", is_active=False))


# --- EncryptedString round trip through a real DB flush/refresh --------


class TestEncryptionAtRest:
    def test_key_round_trips_through_database(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(Apikey(name="vt", key="my-secret-key"))
                await db.commit()

            async with session_factory() as db:
                row = (await db.execute(select(Apikey).where(Apikey.name == "vt"))).scalar_one()
                return row.key

        assert _run(_scenario()) == "my-secret-key"

    def test_key_is_actually_encrypted_on_disk(self, session_factory, async_engine):
        async def _scenario():
            async with session_factory() as db:
                db.add(Apikey(name="vt", key="my-secret-key"))
                await db.commit()

            async with async_engine.connect() as conn:
                result = await conn.execute(text("SELECT key FROM apikeys WHERE name = 'vt'"))
                return result.scalar_one()

        raw_value = _run(_scenario())
        assert raw_value != "my-secret-key"

    def test_empty_key_round_trips_as_empty(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(Apikey(name="vt", key=""))
                await db.commit()

            async with session_factory() as db:
                row = (await db.execute(select(Apikey).where(Apikey.name == "vt"))).scalar_one()
                return row.key

        assert _run(_scenario()) == ""
