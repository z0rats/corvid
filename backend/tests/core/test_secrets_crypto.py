"""Tests use a fixed in-memory Fernet key (monkeypatching the private
_get_fernet accessor) rather than exercising the real file-backed key, so
they never touch this developer's actual <data_dir>/.encryption_key."""

from cryptography.fernet import Fernet

from app.core.security import secrets_crypto
from app.core.security.secrets_crypto import decrypt_value, encrypt_value


def _use_fixed_fernet(monkeypatch):
    fixed = Fernet(Fernet.generate_key())
    monkeypatch.setattr(secrets_crypto, "_get_fernet", lambda: fixed)
    return fixed


def test_encrypt_then_decrypt_round_trips(monkeypatch):
    _use_fixed_fernet(monkeypatch)

    encrypted = encrypt_value("super-secret-api-key")

    assert encrypted != "super-secret-api-key"
    assert decrypt_value(encrypted) == "super-secret-api-key"


def test_encrypt_value_passes_through_empty_string(monkeypatch):
    _use_fixed_fernet(monkeypatch)
    assert encrypt_value("") == ""


def test_decrypt_value_passes_through_empty_string(monkeypatch):
    _use_fixed_fernet(monkeypatch)
    assert decrypt_value("") == ""


def test_decrypt_value_returns_legacy_plaintext_unchanged(monkeypatch):
    """Pre-encryption rows stored plain values, which aren't valid Fernet
    tokens - decrypt_value must return them unchanged instead of raising."""
    _use_fixed_fernet(monkeypatch)

    assert decrypt_value("plain-legacy-value") == "plain-legacy-value"


def test_decrypt_value_with_wrong_key_returns_original_value(monkeypatch):
    """A token encrypted under one key, decrypted under a different one,
    should fail closed (return the ciphertext unchanged) rather than raise."""
    encrypting_fernet = Fernet(Fernet.generate_key())
    monkeypatch.setattr(secrets_crypto, "_get_fernet", lambda: encrypting_fernet)
    token = encrypt_value("secret")

    other_fernet = Fernet(Fernet.generate_key())
    monkeypatch.setattr(secrets_crypto, "_get_fernet", lambda: other_fernet)

    assert decrypt_value(token) == token


def test_derive_fernet_key_is_deterministic_for_same_secret():
    key_a = secrets_crypto._derive_fernet_key("my-secret")
    key_b = secrets_crypto._derive_fernet_key("my-secret")
    assert key_a == key_b


def test_derive_fernet_key_differs_for_different_secrets():
    key_a = secrets_crypto._derive_fernet_key("secret-one")
    key_b = secrets_crypto._derive_fernet_key("secret-two")
    assert key_a != key_b


def test_derive_fernet_key_is_usable_by_fernet():
    key = secrets_crypto._derive_fernet_key("arbitrary length secret value")
    fernet = Fernet(key)
    assert fernet.decrypt(fernet.encrypt(b"payload")) == b"payload"
