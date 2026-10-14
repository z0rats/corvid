"""DB_URL handling: SQLite is the only supported backend (docs/adr/0004-*)."""

import pytest

from app.core.config.settings import DatabaseSettings
from app.core.database import _to_async_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("sqlite:///./data/corvid.db", "sqlite+aiosqlite:///./data/corvid.db"),
        ("sqlite:////abs/corvid.db", "sqlite+aiosqlite:////abs/corvid.db"),
        ("sqlite+aiosqlite:///./data/corvid.db", "sqlite+aiosqlite:///./data/corvid.db"),
    ],
)
def test_sqlite_urls_map_to_aiosqlite(url, expected):
    assert _to_async_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:secret@db/corvid",
        "postgresql+asyncpg://user:secret@db/corvid",
        "mysql://x",
    ],
)
def test_non_sqlite_urls_fail_with_a_clear_message_that_hides_credentials(url):
    with pytest.raises(ValueError, match="SQLite only") as excinfo:
        _to_async_url(url)
    assert "secret" not in str(excinfo.value)


def test_a_leftover_db_pool_recycle_in_env_does_not_break_startup(monkeypatch, tmp_path):
    # DB_POOL_RECYCLE used to be a setting; operators' .env files may still carry it.
    (tmp_path / ".env").write_text("DB_POOL_RECYCLE=3600\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_POOL_RECYCLE", "3600")

    assert DatabaseSettings().url.startswith("sqlite:///")
