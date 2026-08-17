from pydantic import BaseModel, ConfigDict, Field


class RuBusinessCheckSettingsSchema(BaseModel):
    id: int = Field(..., description="Configuration record ID")
    fresh_registration_threshold_days: int = Field(
        ...,
        description="Registration age (days) below which the soft 'fresh registration' flag fires",
    )
    history_retention_days: int = Field(
        ..., description="Days a search is kept before automatic deletion; 0 = unlimited"
    )
    small_claim_amount_threshold: int = Field(
        ...,
        description=(
            "Claim amount (RUB) below which a single resolved arbitration case as "
            "defendant is a soft flag"
        ),
    )
    large_claim_amount_threshold: int = Field(
        ...,
        description=(
            "Claim amount (RUB) above which any arbitration case as defendant is a soft flag"
        ),
    )
    multiple_claims_defendant_threshold: int = Field(
        ...,
        description=(
            "Number of arbitration cases as defendant at/above which the 'multiple "
            "claims' soft flag fires"
        ),
    )
    mass_address_threshold: int = Field(
        ...,
        description="Number of other entities at the same address (pb.nalog.ru) "
        "at/above which the 'mass registration address' soft flag fires",
    )

    model_config = ConfigDict(from_attributes=True)


class RuBusinessCheckSettingsUpdateSchema(BaseModel):
    fresh_registration_threshold_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
        description="Registration age (days) below which the soft 'fresh registration' flag fires",
    )
    history_retention_days: int | None = Field(
        default=None,
        ge=0,
        le=3650,
        description="Days a search is kept before automatic deletion; 0 = unlimited",
    )
    small_claim_amount_threshold: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Claim amount (RUB) below which a single resolved arbitration case as "
            "defendant is a soft flag"
        ),
    )
    large_claim_amount_threshold: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Claim amount (RUB) above which any arbitration case as defendant is a soft flag"
        ),
    )
    multiple_claims_defendant_threshold: int | None = Field(
        default=None,
        ge=1,
        le=100,
        description=(
            "Number of arbitration cases as defendant at/above which the 'multiple "
            "claims' soft flag fires"
        ),
    )
    mass_address_threshold: int | None = Field(
        default=None,
        ge=1,
        le=1000,
        description="Number of other entities at the same address (pb.nalog.ru) "
        "at/above which the 'mass registration address' soft flag fires",
    )
