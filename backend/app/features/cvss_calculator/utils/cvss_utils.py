import logging
from typing import Any, Union

logger = logging.getLogger(__name__)


def calculate_severity_from_score(score: float) -> str:
    """Calculate severity rating from CVSS score."""
    if score >= 9.0:
        return "Critical"
    elif score >= 7.0:
        return "High"
    elif score >= 4.0:
        return "Medium"
    elif score > 0.0:
        return "Low"
    else:
        return "None"


def extract_enum_values_from_metrics(metrics_dict: dict[str, Any]) -> dict[str, Any]:
    """Extract enum values from metrics dictionary, handling both enum objects and plain values."""
    return {
        key: value.value if hasattr(value, 'value') else value 
        for key, value in metrics_dict.items()
        if value is not None
    }


def build_cvss31_vector_from_metrics(
    base_metrics: dict[str, Any],
    temporal_metrics: dict[str, Any] | None = None,
    environmental_metrics: dict[str, Any] | None = None
) -> str:
    """Build CVSS 3.1 vector string from individual metrics."""
    vector_parts = _build_cvss31_base_vector_parts(base_metrics)
    
    if temporal_metrics:
        vector_parts.extend(_build_cvss31_temporal_vector_parts(temporal_metrics))
    
    if environmental_metrics:
        vector_parts.extend(_build_cvss31_environmental_vector_parts(environmental_metrics))
    
    return "/".join(vector_parts)


def build_cvss40_vector_from_metrics(
    base_metrics: dict[str, Any],
    threat_metrics: dict[str, Any] | None = None
) -> str:
    """Build CVSS 4.0 vector string from individual metrics."""
    vector_parts = _build_cvss40_base_vector_parts(base_metrics)
    
    if threat_metrics and threat_metrics.get('exploit_maturity') != "X":
        vector_parts.append(f"E:{threat_metrics['exploit_maturity']}")
    
    return "/".join(vector_parts)


def extract_cvss_scores_and_severities(cvss_obj: Any) -> tuple[float, str, float | None, str | None, float | None, str | None]:
    """Extract scores and severities from CVSS object."""
    base_score = cvss_obj.base_score
    base_severity = calculate_severity_from_score(base_score)
    
    temporal_score = getattr(cvss_obj, 'temporal_score', base_score)
    temporal_severity = calculate_severity_from_score(temporal_score)
    
    environmental_score = getattr(cvss_obj, 'environmental_score', base_score)
    environmental_severity = calculate_severity_from_score(environmental_score)
    
    return (
        base_score,
        base_severity,
        temporal_score if temporal_score != base_score else None,
        temporal_severity if temporal_severity != base_severity else None,
        environmental_score if environmental_score != base_score else None,
        environmental_severity if environmental_severity != base_severity else None
    )


def get_cvss31_metrics_definition() -> dict[str, dict[str, list]]:
    """Get CVSS 3.1 metrics definitions for API responses."""
    return {
        "base_metrics": {
            "attack_vector": ["N", "A", "L", "P"],
            "attack_complexity": ["L", "H"],
            "privileges_required": ["N", "L", "H"],
            "user_interaction": ["N", "R"],
            "scope": ["U", "C"],
            "confidentiality_impact": ["N", "L", "H"],
            "integrity_impact": ["N", "L", "H"],
            "availability_impact": ["N", "L", "H"]
        },
        "temporal_metrics": {
            "exploit_code_maturity": ["X", "U", "P", "F", "H"],
            "remediation_level": ["X", "O", "T", "W", "U"],
            "report_confidence": ["X", "U", "R", "C"]
        },
        "environmental_metrics": {
            "confidentiality_requirement": ["X", "L", "M", "H"],
            "integrity_requirement": ["X", "L", "M", "H"],
            "availability_requirement": ["X", "L", "M", "H"],
            "modified_attack_vector": ["X", "N", "A", "L", "P"],
            "modified_attack_complexity": ["X", "L", "H"],
            "modified_privileges_required": ["X", "N", "L", "H"],
            "modified_user_interaction": ["X", "N", "R"],
            "modified_scope": ["X", "U", "C"],
            "modified_confidentiality_impact": ["X", "N", "L", "H"],
            "modified_integrity_impact": ["X", "N", "L", "H"],
            "modified_availability_impact": ["X", "N", "L", "H"]
        }
    }


def get_cvss40_metrics_definition() -> dict[str, dict[str, list]]:
    """Get CVSS 4.0 metrics definitions for API responses."""
    return {
        "base_metrics": {
            "attack_vector": ["N", "A", "L", "P"],
            "attack_complexity": ["L", "H"],
            "attack_requirements": ["N", "P"],
            "privileges_required": ["N", "L", "H"],
            "user_interaction": ["N", "P", "A"],
            "vulnerable_system_confidentiality": ["N", "L", "H"],
            "vulnerable_system_integrity": ["N", "L", "H"],
            "vulnerable_system_availability": ["N", "L", "H"],
            "subsequent_system_confidentiality": ["N", "L", "H"],
            "subsequent_system_integrity": ["N", "L", "H"],
            "subsequent_system_availability": ["N", "L", "H"]
        },
        "threat_metrics": {
            "exploit_maturity": ["X", "U", "P", "A"]
        }
    }


def validate_cvss_vector_format(vector_string: str, version: str) -> bool:
    """Validate basic CVSS vector string format before processing."""
    if not vector_string or not isinstance(vector_string, str):
        return False
    
    expected_prefix = f"CVSS:{version}"
    if not vector_string.startswith(expected_prefix):
        return False
    
    if "/" not in vector_string:
        return False
    
    return True


def log_calculation_attempt(version: str, calculation_type: str, success: bool, error: str | None = None) -> None:
    """Log CVSS calculation attempts for monitoring."""
    if success:
        logger.info("CVSS %s %s calculation successful", version, calculation_type)
    else:
        logger.error("CVSS %s %s calculation failed: %s", version, calculation_type, error)


def _build_cvss31_base_vector_parts(base_metrics: dict[str, Any]) -> list:
    """Build base vector parts for CVSS 3.1."""
    return [
        "CVSS:3.1",
        f"AV:{base_metrics['attack_vector']}",
        f"AC:{base_metrics['attack_complexity']}",
        f"PR:{base_metrics['privileges_required']}",
        f"UI:{base_metrics['user_interaction']}",
        f"S:{base_metrics['scope']}",
        f"C:{base_metrics['confidentiality_impact']}",
        f"I:{base_metrics['integrity_impact']}",
        f"A:{base_metrics['availability_impact']}"
    ]


def _build_cvss31_temporal_vector_parts(temporal_metrics: dict[str, Any]) -> list:
    """Build temporal vector parts for CVSS 3.1."""
    parts = []
    
    temporal_mappings = [
        ('exploit_code_maturity', 'E'),
        ('remediation_level', 'RL'),
        ('report_confidence', 'RC')
    ]
    
    for field_name, vector_code in temporal_mappings:
        value = temporal_metrics.get(field_name)
        if value and value != "X":
            parts.append(f"{vector_code}:{value}")
    
    return parts


def _build_cvss31_environmental_vector_parts(environmental_metrics: dict[str, Any]) -> list:
    """Build environmental vector parts for CVSS 3.1."""
    parts = []
    
    env_mappings = [
        ('confidentiality_requirement', 'CR'),
        ('integrity_requirement', 'IR'),
        ('availability_requirement', 'AR'),
        ('modified_attack_vector', 'MAV'),
        ('modified_attack_complexity', 'MAC'),
        ('modified_privileges_required', 'MPR'),
        ('modified_user_interaction', 'MUI'),
        ('modified_scope', 'MS'),
        ('modified_confidentiality_impact', 'MC'),
        ('modified_integrity_impact', 'MI'),
        ('modified_availability_impact', 'MA')
    ]
    
    for field_name, vector_code in env_mappings:
        value = environmental_metrics.get(field_name)
        if value and value != "X":
            parts.append(f"{vector_code}:{value}")
    
    return parts


def _build_cvss40_base_vector_parts(base_metrics: dict[str, Any]) -> list:
    """Build base vector parts for CVSS 4.0."""
    return [
        "CVSS:4.0",
        f"AV:{base_metrics['attack_vector']}",
        f"AC:{base_metrics['attack_complexity']}",
        f"AT:{base_metrics['attack_requirements']}",
        f"PR:{base_metrics['privileges_required']}",
        f"UI:{base_metrics['user_interaction']}",
        f"VC:{base_metrics['vulnerable_system_confidentiality']}",
        f"VI:{base_metrics['vulnerable_system_integrity']}",
        f"VA:{base_metrics['vulnerable_system_availability']}",
        f"SC:{base_metrics['subsequent_system_confidentiality']}",
        f"SI:{base_metrics['subsequent_system_integrity']}",
        f"SA:{base_metrics['subsequent_system_availability']}"
    ]
