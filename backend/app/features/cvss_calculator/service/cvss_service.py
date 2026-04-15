import logging
from typing import Any

from cvss import CVSS3, CVSS4

from ..schemas.cvss_schemas import (
    CVSS31Request, CVSS31VectorRequest, CVSSScoreResponse,
    CVSS40Request, CVSS40VectorRequest, CVSS40ScoreResponse,
    VectorValidationResponse, MetricsDefinitionResponse
)
from ..utils.cvss_utils import (
    build_cvss31_vector_from_metrics,
    build_cvss40_vector_from_metrics,
    extract_cvss_scores_and_severities,
    calculate_severity_from_score,
    get_cvss31_metrics_definition,
    get_cvss40_metrics_definition,
    validate_cvss_vector_format,
    log_calculation_attempt,
    extract_enum_values_from_metrics
)

logger = logging.getLogger(__name__)


def calculate_cvss31_from_metrics(request: CVSS31Request) -> CVSSScoreResponse:
    """Calculate CVSS 3.1 score from individual metrics."""
    try:
        metrics_dict = _prepare_cvss31_metrics_dict(request)
        vector_string = build_cvss31_vector_from_metrics(
            metrics_dict["base"], 
            metrics_dict["temporal"], 
            metrics_dict["environmental"]
        )
        
        cvss = CVSS3(vector_string)
        response = _build_cvss31_response(cvss, vector_string)
        
        log_calculation_attempt("3.1", "metrics", True)
        return response
        
    except Exception as e:
        error_msg = f"Invalid CVSS 3.1 metrics: {str(e)}"
        log_calculation_attempt("3.1", "metrics", False, error_msg)
        raise ValueError(error_msg)


def calculate_cvss31_from_vector(request: CVSS31VectorRequest) -> CVSSScoreResponse:
    """Calculate CVSS 3.1 score from vector string."""
    try:
        _validate_vector_string(request.vector_string, "3.1")
        
        cvss = CVSS3(request.vector_string)
        response = _build_cvss31_response(cvss, request.vector_string)
        
        log_calculation_attempt("3.1", "vector", True)
        return response
        
    except Exception as e:
        error_msg = f"Invalid CVSS 3.1 vector string: {str(e)}"
        log_calculation_attempt("3.1", "vector", False, error_msg)
        raise ValueError(error_msg)


def calculate_cvss40_from_metrics(request: CVSS40Request) -> CVSS40ScoreResponse:
    """Calculate CVSS 4.0 score from individual metrics."""
    try:
        metrics_dict = _prepare_cvss40_metrics_dict(request)
        vector_string = build_cvss40_vector_from_metrics(
            metrics_dict["base"], 
            metrics_dict["threat"]
        )
        
        cvss = CVSS4(vector_string)
        response = _build_cvss40_response(cvss, vector_string)
        
        log_calculation_attempt("4.0", "metrics", True)
        return response
        
    except Exception as e:
        error_msg = f"Invalid CVSS 4.0 metrics: {str(e)}"
        log_calculation_attempt("4.0", "metrics", False, error_msg)
        raise ValueError(error_msg)


def calculate_cvss40_from_vector(request: CVSS40VectorRequest) -> CVSS40ScoreResponse:
    """Calculate CVSS 4.0 score from vector string."""
    try:
        _validate_vector_string(request.vector_string, "4.0")
        
        cvss = CVSS4(request.vector_string)
        response = _build_cvss40_response(cvss, request.vector_string)
        
        log_calculation_attempt("4.0", "vector", True)
        return response
        
    except Exception as e:
        error_msg = f"Invalid CVSS 4.0 vector string: {str(e)}"
        log_calculation_attempt("4.0", "vector", False, error_msg)
        raise ValueError(error_msg)


def validate_cvss31_vector(vector_string: str) -> VectorValidationResponse:
    """Validate CVSS 3.1 vector string."""
    try:
        _validate_vector_string(vector_string, "3.1")
        CVSS3(vector_string)
        
        return VectorValidationResponse(
            valid=True,
            vector_string=vector_string
        )
    except Exception as e:
        return VectorValidationResponse(
            valid=False,
            vector_string=vector_string,
            error_message=str(e)
        )


def validate_cvss40_vector(vector_string: str) -> VectorValidationResponse:
    """Validate CVSS 4.0 vector string."""
    try:
        _validate_vector_string(vector_string, "4.0")
        CVSS4(vector_string)
        
        return VectorValidationResponse(
            valid=True,
            vector_string=vector_string
        )
    except Exception as e:
        return VectorValidationResponse(
            valid=False,
            vector_string=vector_string,
            error_message=str(e)
        )


def get_cvss31_metrics() -> MetricsDefinitionResponse:
    """Get CVSS 3.1 metrics definitions."""
    metrics = get_cvss31_metrics_definition()
    return MetricsDefinitionResponse(
        version="3.1",
        base_metrics=metrics["base_metrics"],
        temporal_metrics=metrics["temporal_metrics"],
        environmental_metrics=metrics["environmental_metrics"]
    )


def get_cvss40_metrics() -> MetricsDefinitionResponse:
    """Get CVSS 4.0 metrics definitions."""
    metrics = get_cvss40_metrics_definition()
    return MetricsDefinitionResponse(
        version="4.0",
        base_metrics=metrics["base_metrics"],
        threat_metrics=metrics["threat_metrics"]
    )


def _prepare_cvss31_metrics_dict(request: CVSS31Request) -> dict[str, dict[str, Any] | None]:
    """Prepare CVSS 3.1 metrics dictionary with extracted enum values."""
    base_dict = extract_enum_values_from_metrics(request.base_metrics.model_dump())
    
    temporal_dict = None
    if request.temporal_metrics:
        temporal_dict = extract_enum_values_from_metrics(request.temporal_metrics.model_dump())
    
    environmental_dict = None
    if request.environmental_metrics:
        environmental_dict = extract_enum_values_from_metrics(request.environmental_metrics.model_dump())
    
    return {
        "base": base_dict,
        "temporal": temporal_dict,
        "environmental": environmental_dict
    }


def _prepare_cvss40_metrics_dict(request: CVSS40Request) -> dict[str, dict[str, Any] | None]:
    """Prepare CVSS 4.0 metrics dictionary with extracted enum values."""
    base_dict = extract_enum_values_from_metrics(request.base_metrics.model_dump())
    
    threat_dict = None
    if request.threat_metrics:
        threat_dict = extract_enum_values_from_metrics(request.threat_metrics.model_dump())
    
    return {
        "base": base_dict,
        "threat": threat_dict
    }


def _validate_vector_string(vector_string: str, version: str) -> None:
    """Validate vector string format and raise ValueError if invalid."""
    if not validate_cvss_vector_format(vector_string, version):
        raise ValueError(f"Invalid CVSS {version} vector format")


def _build_cvss31_response(cvss: CVSS3, vector_string: str) -> CVSSScoreResponse:
    """Build CVSS 3.1 response from CVSS object."""
    (base_score, base_severity, temporal_score, temporal_severity, 
     environmental_score, environmental_severity) = extract_cvss_scores_and_severities(cvss)
    
    return CVSSScoreResponse(
        base_score=base_score,
        base_severity=base_severity,
        temporal_score=temporal_score,
        temporal_severity=temporal_severity,
        environmental_score=environmental_score,
        environmental_severity=environmental_severity,
        vector_string=vector_string,
        exploitability_score=getattr(cvss, 'exploitability_score', None),
        impact_score=getattr(cvss, 'impact_score', None)
    )


def _build_cvss40_response(cvss: CVSS4, vector_string: str) -> CVSS40ScoreResponse:
    """Build CVSS 4.0 response from CVSS object."""
    base_score = cvss.base_score
    base_severity = calculate_severity_from_score(base_score)
    
    return CVSS40ScoreResponse(
        base_score=base_score,
        base_severity=base_severity,
        vector_string=vector_string,
        exploitability_score=getattr(cvss, 'exploitability_score', None),
        impact_score=getattr(cvss, 'impact_score', None)
    )
