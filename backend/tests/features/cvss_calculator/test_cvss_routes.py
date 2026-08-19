import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import register_exception_handlers
from app.features.cvss_calculator.routers import cvss_routes

CRITICAL_31_VECTOR = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
CRITICAL_40_VECTOR = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"


@pytest.fixture
def client():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(cvss_routes.router)
    return TestClient(app)


class TestCalculateFromMetrics:
    def test_v31_calculate_returns_the_known_score(self, client):
        response = client.post(
            "/api/cvss/v3.1/calculate",
            json={
                "base_metrics": {
                    "attack_vector": "N",
                    "attack_complexity": "L",
                    "privileges_required": "N",
                    "user_interaction": "N",
                    "scope": "U",
                    "confidentiality_impact": "H",
                    "integrity_impact": "H",
                    "availability_impact": "H",
                }
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["base_score"] == 9.8
        assert body["base_severity"] == "Critical"
        assert body["vector_string"] == CRITICAL_31_VECTOR

    def test_v31_calculate_rejects_a_missing_required_metric_with_422(self, client):
        response = client.post(
            "/api/cvss/v3.1/calculate",
            json={
                "base_metrics": {
                    "attack_vector": "N",
                    "attack_complexity": "L",
                    "privileges_required": "N",
                    "user_interaction": "N",
                    "scope": "U",
                    "confidentiality_impact": "H",
                    "integrity_impact": "H",
                    # availability_impact omitted
                }
            },
        )

        assert response.status_code == 422

    def test_v31_calculate_rejects_an_invalid_enum_value_with_422(self, client):
        response = client.post(
            "/api/cvss/v3.1/calculate",
            json={
                "base_metrics": {
                    "attack_vector": "NOT-A-VALID-VALUE",
                    "attack_complexity": "L",
                    "privileges_required": "N",
                    "user_interaction": "N",
                    "scope": "U",
                    "confidentiality_impact": "H",
                    "integrity_impact": "H",
                    "availability_impact": "H",
                }
            },
        )

        assert response.status_code == 422

    def test_v40_calculate_returns_the_known_score(self, client):
        response = client.post(
            "/api/cvss/v4.0/calculate",
            json={
                "base_metrics": {
                    "attack_vector": "N",
                    "attack_complexity": "L",
                    "attack_requirements": "N",
                    "privileges_required": "N",
                    "user_interaction": "N",
                    "vulnerable_system_confidentiality": "H",
                    "vulnerable_system_integrity": "H",
                    "vulnerable_system_availability": "H",
                    "subsequent_system_confidentiality": "N",
                    "subsequent_system_integrity": "N",
                    "subsequent_system_availability": "N",
                }
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["base_score"] == 9.3
        assert body["vector_string"] == CRITICAL_40_VECTOR


class TestCalculateFromVector:
    def test_v31_calculate_from_vector_returns_the_known_score(self, client):
        response = client.post(
            "/api/cvss/v3.1/calculate-from-vector", json={"vector_string": CRITICAL_31_VECTOR}
        )

        assert response.status_code == 200
        assert response.json()["base_score"] == 9.8

    def test_v31_calculate_from_vector_returns_400_for_a_malformed_vector(self, client):
        response = client.post(
            "/api/cvss/v3.1/calculate-from-vector", json={"vector_string": "not-a-vector"}
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "CVSS_INVALID_INPUT"

    def test_v40_calculate_from_vector_returns_the_known_score(self, client):
        response = client.post(
            "/api/cvss/v4.0/calculate-from-vector", json={"vector_string": CRITICAL_40_VECTOR}
        )

        assert response.status_code == 200
        assert response.json()["base_score"] == 9.3

    def test_v40_calculate_from_vector_returns_400_for_a_malformed_vector(self, client):
        response = client.post(
            "/api/cvss/v4.0/calculate-from-vector", json={"vector_string": "not-a-vector"}
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "CVSS_INVALID_INPUT"


class TestValidateVector:
    def test_v31_validate_vector_reports_a_valid_vector(self, client):
        response = client.post(
            "/api/cvss/v3.1/validate-vector", json={"vector_string": CRITICAL_31_VECTOR}
        )

        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_v31_validate_vector_reports_an_invalid_vector_without_erroring(self, client):
        response = client.post(
            "/api/cvss/v3.1/validate-vector", json={"vector_string": "not-a-vector"}
        )

        assert response.status_code == 200
        assert response.json()["valid"] is False

    def test_v40_validate_vector_reports_a_valid_vector(self, client):
        response = client.post(
            "/api/cvss/v4.0/validate-vector", json={"vector_string": CRITICAL_40_VECTOR}
        )

        assert response.status_code == 200
        assert response.json()["valid"] is True


class TestMetricsDefinitions:
    def test_v31_metrics_returns_all_three_groups(self, client):
        response = client.get("/api/cvss/metrics/v3.1")

        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "3.1"
        assert "base_metrics" in body
        assert "temporal_metrics" in body
        assert "environmental_metrics" in body

    def test_v40_metrics_returns_base_and_threat_groups(self, client):
        response = client.get("/api/cvss/metrics/v4.0")

        assert response.status_code == 200
        body = response.json()
        assert body["version"] == "4.0"
        assert "threat_metrics" in body
