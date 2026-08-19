import pytest

from app.features.cvss_calculator.schemas.cvss_schemas import (
    CVSS31BaseMetrics,
    CVSS31Request,
    CVSS31TemporalMetrics,
    CVSS31VectorRequest,
    CVSS40BaseMetrics,
    CVSS40Request,
    CVSS40VectorRequest,
)
from app.features.cvss_calculator.service import cvss_service

# CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H is a well-known 9.8 Critical vector
# (real base_score computed by the installed `cvss` package, not hand-derived).
CRITICAL_31_METRICS = CVSS31BaseMetrics(
    attack_vector="N",
    attack_complexity="L",
    privileges_required="N",
    user_interaction="N",
    scope="U",
    confidentiality_impact="H",
    integrity_impact="H",
    availability_impact="H",
)
CRITICAL_31_VECTOR = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

CRITICAL_40_METRICS = CVSS40BaseMetrics(
    attack_vector="N",
    attack_complexity="L",
    attack_requirements="N",
    privileges_required="N",
    user_interaction="N",
    vulnerable_system_confidentiality="H",
    vulnerable_system_integrity="H",
    vulnerable_system_availability="H",
    subsequent_system_confidentiality="N",
    subsequent_system_integrity="N",
    subsequent_system_availability="N",
)
CRITICAL_40_VECTOR = "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"


class TestCalculateCvss31FromMetrics:
    def test_computes_the_known_score_and_vector_for_a_critical_vulnerability(self):
        response = cvss_service.calculate_cvss31_from_metrics(
            CVSS31Request(base_metrics=CRITICAL_31_METRICS)
        )

        assert response.base_score == 9.8
        assert response.base_severity == "Critical"
        assert response.vector_string == CRITICAL_31_VECTOR
        assert response.temporal_score is None
        assert response.environmental_score is None
        # Regression check: these come from the `cvss` library's `esc`/`isc`
        # attributes, not `exploitability_score`/`impact_score` (which don't
        # exist on its CVSS3 objects and previously left these always None).
        assert response.exploitability_score == pytest.approx(3.887, abs=0.001)
        assert response.impact_score == pytest.approx(5.873, abs=0.001)

    def test_temporal_metrics_lower_the_score_and_are_reported_separately_from_base(self):
        response = cvss_service.calculate_cvss31_from_metrics(
            CVSS31Request(
                base_metrics=CRITICAL_31_METRICS,
                temporal_metrics=CVSS31TemporalMetrics(
                    exploit_code_maturity="P", remediation_level="O", report_confidence="C"
                ),
            )
        )

        assert response.base_score == 9.8
        assert response.temporal_score is not None
        assert response.temporal_score < response.base_score

    def test_missing_mandatory_metric_raises_value_error(self):
        # pydantic requires every base_metrics field at construction time, so the
        # only way to reach this path is mutating one to None post-construction -
        # extract_enum_values_from_metrics then drops it, and vector-building fails.
        incomplete = CVSS31Request(base_metrics=CRITICAL_31_METRICS)
        incomplete.base_metrics.attack_vector = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="Invalid CVSS 3.1 metrics"):
            cvss_service.calculate_cvss31_from_metrics(incomplete)


class TestCalculateCvss31FromVector:
    def test_computes_the_known_score_from_a_vector_string(self):
        response = cvss_service.calculate_cvss31_from_vector(
            CVSS31VectorRequest(vector_string=CRITICAL_31_VECTOR)
        )

        assert response.base_score == 9.8
        assert response.base_severity == "Critical"

    def test_rejects_a_vector_with_the_wrong_version_prefix(self):
        with pytest.raises(ValueError, match="Invalid CVSS 3.1 vector"):
            cvss_service.calculate_cvss31_from_vector(
                CVSS31VectorRequest(vector_string=CRITICAL_40_VECTOR)
            )

    def test_rejects_a_vector_missing_mandatory_metrics(self):
        with pytest.raises(ValueError, match="Invalid CVSS 3.1 vector"):
            cvss_service.calculate_cvss31_from_vector(
                CVSS31VectorRequest(vector_string="CVSS:3.1/AV:N/AC:L")
            )


class TestCalculateCvss40FromMetrics:
    def test_computes_the_known_score_and_vector_for_a_critical_vulnerability(self):
        response = cvss_service.calculate_cvss40_from_metrics(
            CVSS40Request(base_metrics=CRITICAL_40_METRICS)
        )

        assert response.base_score == 9.3
        assert response.base_severity == "Critical"
        assert response.vector_string == CRITICAL_40_VECTOR
        # The installed `cvss` package doesn't expose subscores for v4.0.
        assert response.exploitability_score is None
        assert response.impact_score is None


class TestCalculateCvss40FromVector:
    def test_computes_the_known_score_from_a_vector_string(self):
        response = cvss_service.calculate_cvss40_from_vector(
            CVSS40VectorRequest(vector_string=CRITICAL_40_VECTOR)
        )

        assert response.base_score == 9.3
        assert response.base_severity == "Critical"

    def test_rejects_a_vector_missing_mandatory_metrics(self):
        with pytest.raises(ValueError, match="Invalid CVSS 4.0 vector"):
            cvss_service.calculate_cvss40_from_vector(
                CVSS40VectorRequest(vector_string="CVSS:4.0/AV:N")
            )


class TestValidateCvss31Vector:
    def test_valid_vector_reports_valid_with_no_error(self):
        result = cvss_service.validate_cvss31_vector(CRITICAL_31_VECTOR)

        assert result.valid is True
        assert result.error_message is None

    def test_invalid_vector_reports_invalid_with_an_error_message(self):
        result = cvss_service.validate_cvss31_vector("CVSS:3.1/AV:N")

        assert result.valid is False
        assert result.error_message is not None


class TestValidateCvss40Vector:
    def test_valid_vector_reports_valid_with_no_error(self):
        result = cvss_service.validate_cvss40_vector(CRITICAL_40_VECTOR)

        assert result.valid is True
        assert result.error_message is None

    def test_wrong_version_prefix_reports_invalid(self):
        result = cvss_service.validate_cvss40_vector(CRITICAL_31_VECTOR)

        assert result.valid is False


class TestGetMetricsDefinitions:
    def test_cvss31_definition_is_tagged_with_its_version(self):
        response = cvss_service.get_cvss31_metrics()
        assert response.version == "3.1"
        assert response.temporal_metrics is not None
        assert response.threat_metrics is None

    def test_cvss40_definition_is_tagged_with_its_version(self):
        response = cvss_service.get_cvss40_metrics()
        assert response.version == "4.0"
        assert response.threat_metrics is not None
        assert response.temporal_metrics is None
