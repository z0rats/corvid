from fastapi import APIRouter

from ..schemas.cvss_schemas import (
    CVSS31Request, CVSS31VectorRequest, CVSSScoreResponse,
    CVSS40Request, CVSS40VectorRequest, CVSS40ScoreResponse,
    VectorValidationResponse, MetricsDefinitionResponse
)
from ..service import cvss_service

router = APIRouter(
    prefix="/api/cvss",
    tags=["CVSS Calculator"],
)


@router.post(
    "/v3.1/calculate",
    response_model=CVSSScoreResponse,
    response_model_exclude_none=True,
    summary="Calculate CVSS 3.1 score from metrics",
    description="Calculate CVSS 3.1 score from individual base, temporal, and environmental metrics. Returns the calculated score, severity rating, and vector string.",
)
def calculate_cvss31_from_metrics(request: CVSS31Request) -> CVSSScoreResponse:
    return cvss_service.calculate_cvss31_from_metrics(request)


@router.post(
    "/v3.1/calculate-from-vector",
    response_model=CVSSScoreResponse,
    response_model_exclude_none=True,
    summary="Calculate CVSS 3.1 score from vector string",
    description="Calculate CVSS 3.1 score from a complete vector string. Parses the vector and returns calculated scores and severity ratings.",
)
def calculate_cvss31_from_vector(request: CVSS31VectorRequest) -> CVSSScoreResponse:
    return cvss_service.calculate_cvss31_from_vector(request)


@router.post(
    "/v3.1/validate-vector",
    response_model=VectorValidationResponse,
    response_model_exclude_none=True,
    summary="Validate CVSS 3.1 vector string",
    description="Validate whether a CVSS 3.1 vector string is properly formatted and contains valid metric values.",
)
def validate_cvss31_vector(request: CVSS31VectorRequest) -> VectorValidationResponse:
    return cvss_service.validate_cvss31_vector(request.vector_string)


@router.post(
    "/v4.0/calculate",
    response_model=CVSS40ScoreResponse,
    response_model_exclude_none=True,
    summary="Calculate CVSS 4.0 score from metrics",
    description="Calculate CVSS 4.0 score from individual base and threat metrics. Returns the calculated score, severity rating, and vector string.",
)
def calculate_cvss40_from_metrics(request: CVSS40Request) -> CVSS40ScoreResponse:
    return cvss_service.calculate_cvss40_from_metrics(request)


@router.post(
    "/v4.0/calculate-from-vector",
    response_model=CVSS40ScoreResponse,
    response_model_exclude_none=True,
    summary="Calculate CVSS 4.0 score from vector string",
    description="Calculate CVSS 4.0 score from a complete vector string. Parses the vector and returns calculated scores and severity ratings.",
)
def calculate_cvss40_from_vector(request: CVSS40VectorRequest) -> CVSS40ScoreResponse:
    return cvss_service.calculate_cvss40_from_vector(request)


@router.post(
    "/v4.0/validate-vector",
    response_model=VectorValidationResponse,
    response_model_exclude_none=True,
    summary="Validate CVSS 4.0 vector string",
    description="Validate whether a CVSS 4.0 vector string is properly formatted and contains valid metric values.",
)
def validate_cvss40_vector(request: CVSS40VectorRequest) -> VectorValidationResponse:
    return cvss_service.validate_cvss40_vector(request.vector_string)


@router.get(
    "/metrics/v3.1",
    response_model=MetricsDefinitionResponse,
    response_model_exclude_none=True,
    summary="Get CVSS 3.1 metrics definitions",
    description="Retrieve available CVSS 3.1 metrics and their possible values for building user interfaces or validation.",
)
def get_cvss31_metrics() -> MetricsDefinitionResponse:
    return cvss_service.get_cvss31_metrics()


@router.get(
    "/metrics/v4.0",
    response_model=MetricsDefinitionResponse,
    response_model_exclude_none=True,
    summary="Get CVSS 4.0 metrics definitions",
    description="Retrieve available CVSS 4.0 metrics and their possible values for building user interfaces or validation.",
)
def get_cvss40_metrics() -> MetricsDefinitionResponse:
    return cvss_service.get_cvss40_metrics()
