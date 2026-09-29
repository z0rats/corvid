import asyncio

from app.features.instagram_search.service import instagram_health_service


def _run(coro):
    return asyncio.run(coro)


def test_get_installed_version_returns_the_pinned_version():
    assert instagram_health_service.get_installed_version() == "4.15.3"


def test_get_health_reports_version_and_session_status(monkeypatch):
    async def _fake_fetch_latest(package_name, timeout_seconds=5.0):
        assert package_name == "instaloader"
        return "4.15.3"

    async def _fake_is_session_configured(db):
        return True

    monkeypatch.setattr(instagram_health_service, "fetch_latest_pypi_version", _fake_fetch_latest)
    monkeypatch.setattr(
        instagram_health_service, "is_session_configured", _fake_is_session_configured
    )

    result = _run(instagram_health_service.get_health(db=None))

    assert result.installed_version == "4.15.3"
    assert result.latest_pypi_version == "4.15.3"
    assert result.update_available is False
    assert result.session_configured is True


def test_get_health_survives_pypi_check_failure(monkeypatch):
    async def _fake_fetch_latest(package_name, timeout_seconds=5.0):
        return None

    async def _fake_is_session_configured(db):
        return False

    monkeypatch.setattr(instagram_health_service, "fetch_latest_pypi_version", _fake_fetch_latest)
    monkeypatch.setattr(
        instagram_health_service, "is_session_configured", _fake_is_session_configured
    )

    result = _run(instagram_health_service.get_health(db=None))

    assert result.latest_pypi_version is None
    assert result.update_available is None
    assert result.session_configured is False
