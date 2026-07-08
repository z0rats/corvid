"""Encryption at rest for sensitive settings values (e.g. third-party API keys).

Uses Fernet (AES-128-CBC + HMAC) symmetric encryption. The key comes from
SECURITY_ENCRYPTION_KEY if set; otherwise one is generated once and persisted to
`<data_dir>/.encryption_key` (mode 0600) so it survives restarts. Losing that
file makes previously encrypted values permanently unreadable, so back it up
alongside the database, or set SECURITY_ENCRYPTION_KEY explicitly for portable
deployments.
"""
import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config.settings import settings
from app.core.security.persisted_secret import load_or_create_secret_file

logger = logging.getLogger(__name__)

_KEY_FILE_NAME = ".encryption_key"


def _derive_fernet_key(secret: str) -> bytes:
    """Turn an arbitrary-length secret into a valid 32-byte urlsafe Fernet key."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _load_or_create_key_file() -> bytes:
    value, created = load_or_create_secret_file(
        _KEY_FILE_NAME, lambda: Fernet.generate_key().decode("utf-8")
    )
    if created:
        logger.warning(
            "Generated a new encryption key at %s/%s to encrypt API keys at rest. "
            "Back this file up together with the database, or set SECURITY_ENCRYPTION_KEY "
            "to a stable secret for portable/reproducible deployments.",
            settings.data_dir, _KEY_FILE_NAME,
        )
    return value.encode("utf-8")


@lru_cache
def _get_fernet() -> Fernet:
    secret = settings.security.encryption_key
    key = _derive_fernet_key(secret) if secret else _load_or_create_key_file()
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a plaintext string. Empty strings pass through unchanged."""
    if not value:
        return value
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str) -> str:
    """Decrypt a value produced by `encrypt_value`.

    Values written before encryption was introduced aren't valid Fernet tokens,
    so decryption fails and the original value is returned unchanged - old
    installs keep working, and the value gets encrypted next time it's saved.
    """
    if not value:
        return value
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return value
