from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# CVSS 3.1 Enums
class AttackVector31(str, Enum):
    """Attack Vector values for CVSS 3.1."""
    NETWORK = "N"
    ADJACENT = "A"
    LOCAL = "L"
    PHYSICAL = "P"


class AttackComplexity31(str, Enum):
    """Attack Complexity values for CVSS 3.1."""
    LOW = "L"
    HIGH = "H"


class PrivilegesRequired31(str, Enum):
    """Privileges Required values for CVSS 3.1."""
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class UserInteraction31(str, Enum):
    """User Interaction values for CVSS 3.1."""
    NONE = "N"
    REQUIRED = "R"


class Scope31(str, Enum):
    """Scope values for CVSS 3.1."""
    UNCHANGED = "U"
    CHANGED = "C"


class Impact31(str, Enum):
    """Impact values for CVSS 3.1 (Confidentiality, Integrity, Availability)."""
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class ExploitCodeMaturity31(str, Enum):
    """Exploit Code Maturity values for CVSS 3.1 temporal metrics."""
    NOT_DEFINED = "X"
    UNPROVEN = "U"
    PROOF_OF_CONCEPT = "P"
    FUNCTIONAL = "F"
    HIGH = "H"


class RemediationLevel31(str, Enum):
    """Remediation Level values for CVSS 3.1 temporal metrics."""
    NOT_DEFINED = "X"
    OFFICIAL_FIX = "O"
    TEMPORARY_FIX = "T"
    WORKAROUND = "W"
    UNAVAILABLE = "U"


class ReportConfidence31(str, Enum):
    """Report Confidence values for CVSS 3.1 temporal metrics."""
    NOT_DEFINED = "X"
    UNKNOWN = "U"
    REASONABLE = "R"
    CONFIRMED = "C"


class SecurityRequirement31(str, Enum):
    """Security Requirement values for CVSS 3.1 environmental metrics."""
    NOT_DEFINED = "X"
    LOW = "L"
    MEDIUM = "M"
    HIGH = "H"


# CVSS 4.0 Enums
class AttackVector40(str, Enum):
    """Attack Vector values for CVSS 4.0."""
    NETWORK = "N"
    ADJACENT = "A"
    LOCAL = "L"
    PHYSICAL = "P"


class AttackComplexity40(str, Enum):
    """Attack Complexity values for CVSS 4.0."""
    LOW = "L"
    HIGH = "H"


class AttackRequirements40(str, Enum):
    """Attack Requirements values for CVSS 4.0."""
    NONE = "N"
    PRESENT = "P"


class PrivilegesRequired40(str, Enum):
    """Privileges Required values for CVSS 4.0."""
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class UserInteraction40(str, Enum):
    """User Interaction values for CVSS 4.0."""
    NONE = "N"
    PASSIVE = "P"
    ACTIVE = "A"


class SystemImpact40(str, Enum):
    """System Impact values for CVSS 4.0 (both vulnerable and subsequent systems)."""
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class ExploitMaturity40(str, Enum):
    """Exploit Maturity values for CVSS 4.0 threat metrics."""
    NOT_DEFINED = "X"
    UNREPORTED = "U"
    PROOF_OF_CONCEPT = "P"
    ATTACKED = "A"


# CVSS 3.1 Request Models
class CVSS31BaseMetrics(BaseModel):
    """Base metrics required for CVSS 3.1 score calculation."""
    
    attack_vector: AttackVector31 = Field(
        ..., 
        description="The attack vector component describes how the vulnerability is exploited"
    )
    attack_complexity: AttackComplexity31 = Field(
        ..., 
        description="The attack complexity component describes the conditions beyond the attacker's control"
    )
    privileges_required: PrivilegesRequired31 = Field(
        ..., 
        description="The privileges required component describes the level of privileges an attacker must possess"
    )
    user_interaction: UserInteraction31 = Field(
        ..., 
        description="The user interaction component captures the requirement for a human user to participate in the attack"
    )
    scope: Scope31 = Field(
        ..., 
        description="The scope component captures whether a vulnerability affects resources beyond its security scope"
    )
    confidentiality_impact: Impact31 = Field(
        ..., 
        description="The confidentiality impact component measures the impact to the confidentiality of information"
    )
    integrity_impact: Impact31 = Field(
        ..., 
        description="The integrity impact component measures the impact to integrity of a successfully exploited vulnerability"
    )
    availability_impact: Impact31 = Field(
        ..., 
        description="The availability impact component measures the impact to the availability of the impacted component"
    )


class CVSS31TemporalMetrics(BaseModel):
    """Optional temporal metrics for CVSS 3.1 that change over time."""
    
    exploit_code_maturity: ExploitCodeMaturity31 = Field(
        default=ExploitCodeMaturity31.NOT_DEFINED,
        description="The exploit code maturity metric measures the likelihood of the vulnerability being attacked"
    )
    remediation_level: RemediationLevel31 = Field(
        default=RemediationLevel31.NOT_DEFINED,
        description="The remediation level metric measures the level of remediation available for the vulnerability"
    )
    report_confidence: ReportConfidence31 = Field(
        default=ReportConfidence31.NOT_DEFINED,
        description="The report confidence metric measures the degree of confidence in the existence of the vulnerability"
    )


class CVSS31EnvironmentalMetrics(BaseModel):
    """Optional environmental metrics for CVSS 3.1 that are specific to a user's environment."""
    
    confidentiality_requirement: SecurityRequirement31 = Field(
        default=SecurityRequirement31.NOT_DEFINED,
        description="The confidentiality requirement metric enables the analyst to customize the score"
    )
    integrity_requirement: SecurityRequirement31 = Field(
        default=SecurityRequirement31.NOT_DEFINED,
        description="The integrity requirement metric enables the analyst to customize the score"
    )
    availability_requirement: SecurityRequirement31 = Field(
        default=SecurityRequirement31.NOT_DEFINED,
        description="The availability requirement metric enables the analyst to customize the score"
    )
    modified_attack_vector: AttackVector31 | None = Field(
        default=None,
        description="Modified attack vector for environmental scoring"
    )
    modified_attack_complexity: AttackComplexity31 | None = Field(
        default=None,
        description="Modified attack complexity for environmental scoring"
    )
    modified_privileges_required: PrivilegesRequired31 | None = Field(
        default=None,
        description="Modified privileges required for environmental scoring"
    )
    modified_user_interaction: UserInteraction31 | None = Field(
        default=None,
        description="Modified user interaction for environmental scoring"
    )
    modified_scope: Scope31 | None = Field(
        default=None,
        description="Modified scope for environmental scoring"
    )
    modified_confidentiality_impact: Impact31 | None = Field(
        default=None,
        description="Modified confidentiality impact for environmental scoring"
    )
    modified_integrity_impact: Impact31 | None = Field(
        default=None,
        description="Modified integrity impact for environmental scoring"
    )
    modified_availability_impact: Impact31 | None = Field(
        default=None,
        description="Modified availability impact for environmental scoring"
    )


class CVSS31Request(BaseModel):
    """Request model for calculating CVSS 3.1 scores from individual metrics."""
    
    base_metrics: CVSS31BaseMetrics = Field(
        ..., 
        description="Required base metrics for CVSS 3.1 calculation"
    )
    temporal_metrics: CVSS31TemporalMetrics | None = Field(
        default=None,
        description="Optional temporal metrics that change over time"
    )
    environmental_metrics: CVSS31EnvironmentalMetrics | None = Field(
        default=None,
        description="Optional environmental metrics specific to the user's environment"
    )


class CVSS31VectorRequest(BaseModel):
    """Request model for calculating CVSS 3.1 scores from vector string."""
    
    vector_string: str = Field(
        ..., 
        description="CVSS 3.1 vector string (e.g., 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H')",
        min_length=1
    )


# CVSS 4.0 Request Models
class CVSS40BaseMetrics(BaseModel):
    """Base metrics required for CVSS 4.0 score calculation."""
    
    attack_vector: AttackVector40 = Field(
        ..., 
        description="The attack vector component describes how the vulnerability is exploited"
    )
    attack_complexity: AttackComplexity40 = Field(
        ..., 
        description="The attack complexity component describes the conditions beyond the attacker's control"
    )
    attack_requirements: AttackRequirements40 = Field(
        ..., 
        description="The attack requirements component captures the prerequisite deployment and execution conditions"
    )
    privileges_required: PrivilegesRequired40 = Field(
        ..., 
        description="The privileges required component describes the level of privileges an attacker must possess"
    )
    user_interaction: UserInteraction40 = Field(
        ..., 
        description="The user interaction component captures the requirement for a human user to participate in the attack"
    )
    vulnerable_system_confidentiality: SystemImpact40 = Field(
        ..., 
        description="The impact to the confidentiality of information managed by the vulnerable system"
    )
    vulnerable_system_integrity: SystemImpact40 = Field(
        ..., 
        description="The impact to the integrity of information managed by the vulnerable system"
    )
    vulnerable_system_availability: SystemImpact40 = Field(
        ..., 
        description="The impact to the availability of information managed by the vulnerable system"
    )
    subsequent_system_confidentiality: SystemImpact40 = Field(
        ..., 
        description="The impact to the confidentiality of information managed by subsequent systems"
    )
    subsequent_system_integrity: SystemImpact40 = Field(
        ..., 
        description="The impact to the integrity of information managed by subsequent systems"
    )
    subsequent_system_availability: SystemImpact40 = Field(
        ..., 
        description="The impact to the availability of information managed by subsequent systems"
    )


class CVSS40ThreatMetrics(BaseModel):
    """Optional threat metrics for CVSS 4.0."""
    
    exploit_maturity: ExploitMaturity40 = Field(
        default=ExploitMaturity40.NOT_DEFINED,
        description="The exploit maturity metric measures the likelihood of the vulnerability being attacked"
    )


class CVSS40Request(BaseModel):
    """Request model for calculating CVSS 4.0 scores from individual metrics."""
    
    base_metrics: CVSS40BaseMetrics = Field(
        ..., 
        description="Required base metrics for CVSS 4.0 calculation"
    )
    threat_metrics: CVSS40ThreatMetrics | None = Field(
        default=None,
        description="Optional threat metrics for CVSS 4.0"
    )


class CVSS40VectorRequest(BaseModel):
    """Request model for calculating CVSS 4.0 scores from vector string."""
    
    vector_string: str = Field(
        ..., 
        description="CVSS 4.0 vector string (e.g., 'CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N')",
        min_length=1
    )


# Response Models
class CVSSScoreResponse(BaseModel):
    """Response model for CVSS 3.1 score calculations."""
    
    base_score: float = Field(
        ..., 
        description="The base CVSS score (0.0-10.0)",
        ge=0.0,
        le=10.0
    )
    base_severity: str = Field(
        ..., 
        description="The severity rating based on the base score (None, Low, Medium, High, Critical)"
    )
    temporal_score: float | None = Field(
        default=None,
        description="The temporal CVSS score if temporal metrics were provided",
        ge=0.0,
        le=10.0
    )
    temporal_severity: str | None = Field(
        default=None,
        description="The severity rating based on the temporal score"
    )
    environmental_score: float | None = Field(
        default=None,
        description="The environmental CVSS score if environmental metrics were provided",
        ge=0.0,
        le=10.0
    )
    environmental_severity: str | None = Field(
        default=None,
        description="The severity rating based on the environmental score"
    )
    vector_string: str = Field(
        ..., 
        description="The complete CVSS vector string"
    )
    exploitability_score: float | None = Field(
        default=None,
        description="The exploitability subscore"
    )
    impact_score: float | None = Field(
        default=None,
        description="The impact subscore"
    )


class CVSS40ScoreResponse(BaseModel):
    """Response model for CVSS 4.0 score calculations."""
    
    base_score: float = Field(
        ..., 
        description="The base CVSS 4.0 score (0.0-10.0)",
        ge=0.0,
        le=10.0
    )
    base_severity: str = Field(
        ..., 
        description="The severity rating based on the base score (None, Low, Medium, High, Critical)"
    )
    vector_string: str = Field(
        ..., 
        description="The complete CVSS 4.0 vector string"
    )
    exploitability_score: float | None = Field(
        default=None,
        description="The exploitability subscore"
    )
    impact_score: float | None = Field(
        default=None,
        description="The impact subscore"
    )


class VectorValidationResponse(BaseModel):
    """Response model for vector string validation."""
    
    valid: bool = Field(
        ..., 
        description="Whether the vector string is valid"
    )
    vector_string: str = Field(
        ..., 
        description="The vector string that was validated"
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if validation failed"
    )


class MetricsDefinitionResponse(BaseModel):
    """Response model for available metrics definitions."""
    
    version: str = Field(
        ..., 
        description="CVSS version (3.1 or 4.0)"
    )
    base_metrics: dict = Field(
        ..., 
        description="Available base metrics and their possible values"
    )
    temporal_metrics: dict | None = Field(
        default=None,
        description="Available temporal metrics and their possible values"
    )
    environmental_metrics: dict | None = Field(
        default=None,
        description="Available environmental metrics and their possible values"
    )
    threat_metrics: dict | None = Field(
        default=None,
        description="Available threat metrics and their possible values (CVSS 4.0 only)"
    )
