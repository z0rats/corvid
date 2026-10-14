"""docker-compose.yaml (build from source) and docker-compose.prod.yaml (install.sh) must keep
identical healthchecks: install.sh's `up --wait` fails the whole install if one never turns
healthy, and the prod file is not exercised by CI's docker-build smoke test."""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_COMPOSE = REPO_ROOT / "docker-compose.yaml"
PROD_COMPOSE = REPO_ROOT / "docker-compose.prod.yaml"
SERVICES = ("backend", "frontend")


def _healthcheck(path: Path, service: str) -> dict:
    return yaml.safe_load(path.read_text())["services"][service]["healthcheck"]


@pytest.mark.parametrize("service", SERVICES)
def test_prod_healthcheck_matches_dev(service):
    assert _healthcheck(PROD_COMPOSE, service) == _healthcheck(DEV_COMPOSE, service)


@pytest.mark.parametrize("path", [DEV_COMPOSE, PROD_COMPOSE], ids=lambda p: p.name)
@pytest.mark.parametrize("service", SERVICES)
def test_healthcheck_avoids_localhost(path, service):
    # Inside the alpine-based frontend image `localhost` resolves to ::1 first, while nginx
    # listens on IPv4 only - the check then never passes. 127.0.0.1 is unambiguous.
    assert "//localhost" not in " ".join(_healthcheck(path, service)["test"])


@pytest.mark.parametrize("service", SERVICES)
def test_healthcheck_probes_fast_during_startup(service):
    # Without start_interval the first probe waits a full `interval` (30s), so `up --wait`
    # and the frontend's depends_on: service_healthy stall for ~a minute on every start.
    assert "start_interval" in _healthcheck(PROD_COMPOSE, service)
