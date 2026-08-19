from types import SimpleNamespace

from app.features.cvss_calculator.utils.cvss_utils import (
    build_cvss31_vector_from_metrics,
    build_cvss40_vector_from_metrics,
    calculate_severity_from_score,
    extract_cvss_scores_and_severities,
    extract_enum_values_from_metrics,
    get_cvss31_metrics_definition,
    get_cvss40_metrics_definition,
    validate_cvss_vector_format,
)


class TestCalculateSeverityFromScore:
    def test_zero_is_none(self):
        assert calculate_severity_from_score(0.0) == "None"

    def test_just_above_zero_is_low(self):
        assert calculate_severity_from_score(0.1) == "Low"

    def test_boundary_values_take_the_higher_band(self):
        assert calculate_severity_from_score(3.9) == "Low"
        assert calculate_severity_from_score(4.0) == "Medium"
        assert calculate_severity_from_score(6.9) == "Medium"
        assert calculate_severity_from_score(7.0) == "High"
        assert calculate_severity_from_score(8.9) == "High"
        assert calculate_severity_from_score(9.0) == "Critical"

    def test_max_score_is_critical(self):
        assert calculate_severity_from_score(10.0) == "Critical"


class TestExtractEnumValuesFromMetrics:
    def test_unwraps_enum_like_objects_via_their_value_attribute(self):
        fake_enum = SimpleNamespace(value="N")
        result = extract_enum_values_from_metrics({"attack_vector": fake_enum, "scope": "U"})
        assert result == {"attack_vector": "N", "scope": "U"}

    def test_drops_none_values(self):
        result = extract_enum_values_from_metrics({"a": "N", "b": None})
        assert result == {"a": "N"}


class TestBuildCvss31VectorFromMetrics:
    base_metrics = {
        "attack_vector": "N",
        "attack_complexity": "L",
        "privileges_required": "N",
        "user_interaction": "N",
        "scope": "U",
        "confidentiality_impact": "H",
        "integrity_impact": "H",
        "availability_impact": "H",
    }

    def test_builds_base_only_vector_when_no_optional_metrics_given(self):
        vector = build_cvss31_vector_from_metrics(self.base_metrics)
        assert vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

    def test_appends_only_non_default_temporal_metrics(self):
        vector = build_cvss31_vector_from_metrics(
            self.base_metrics,
            temporal_metrics={
                "exploit_code_maturity": "P",
                "remediation_level": "X",
                "report_confidence": "C",
            },
        )
        assert vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/E:P/RC:C"

    def test_appends_only_non_default_environmental_metrics(self):
        vector = build_cvss31_vector_from_metrics(
            self.base_metrics,
            environmental_metrics={
                "confidentiality_requirement": "H",
                "integrity_requirement": "X",
                "modified_attack_vector": "X",
            },
        )
        assert vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H/CR:H"


class TestBuildCvss40VectorFromMetrics:
    base_metrics = {
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

    def test_builds_base_only_vector_when_no_threat_metrics_given(self):
        vector = build_cvss40_vector_from_metrics(self.base_metrics)
        assert vector == "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"

    def test_appends_exploit_maturity_when_not_the_default(self):
        vector = build_cvss40_vector_from_metrics(
            self.base_metrics, threat_metrics={"exploit_maturity": "A"}
        )
        assert vector.endswith("/E:A")

    def test_omits_exploit_maturity_when_the_default_not_defined(self):
        vector = build_cvss40_vector_from_metrics(
            self.base_metrics, threat_metrics={"exploit_maturity": "X"}
        )
        assert "E:" not in vector


class TestExtractCvssScoresAndSeverities:
    def test_returns_none_for_temporal_and_environmental_when_they_match_base(self):
        cvss_obj = SimpleNamespace(base_score=9.8, temporal_score=9.8, environmental_score=9.8)

        result = extract_cvss_scores_and_severities(cvss_obj)

        assert result == (9.8, "Critical", None, None, None, None)

    def test_returns_temporal_and_environmental_when_they_differ_from_base(self):
        cvss_obj = SimpleNamespace(base_score=9.8, temporal_score=8.8, environmental_score=6.5)

        result = extract_cvss_scores_and_severities(cvss_obj)

        assert result == (9.8, "Critical", 8.8, "High", 6.5, "Medium")

    def test_falls_back_to_base_score_when_the_object_has_no_temporal_or_environmental_score(self):
        cvss_obj = SimpleNamespace(base_score=5.0)

        result = extract_cvss_scores_and_severities(cvss_obj)

        assert result == (5.0, "Medium", None, None, None, None)


class TestValidateCvssVectorFormat:
    def test_accepts_a_well_formed_vector(self):
        assert validate_cvss_vector_format("CVSS:3.1/AV:N/AC:L", "3.1") is True

    def test_rejects_empty_or_non_string_input(self):
        assert validate_cvss_vector_format("", "3.1") is False
        assert validate_cvss_vector_format(None, "3.1") is False

    def test_rejects_the_wrong_version_prefix(self):
        assert validate_cvss_vector_format("CVSS:4.0/AV:N/AC:L", "3.1") is False

    def test_rejects_a_vector_with_no_metric_separators(self):
        assert validate_cvss_vector_format("CVSS:3.1", "3.1") is False


class TestMetricsDefinitions:
    def test_cvss31_definition_covers_base_temporal_and_environmental_groups(self):
        definition = get_cvss31_metrics_definition()
        assert set(definition) == {"base_metrics", "temporal_metrics", "environmental_metrics"}
        assert definition["base_metrics"]["attack_vector"] == ["N", "A", "L", "P"]

    def test_cvss40_definition_covers_base_and_threat_groups(self):
        definition = get_cvss40_metrics_definition()
        assert set(definition) == {"base_metrics", "threat_metrics"}
        assert definition["threat_metrics"]["exploit_maturity"] == ["X", "U", "P", "A"]
