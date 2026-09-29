from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

FRESH_REGISTRATION_THRESHOLD_DAYS_DEFAULT = 365
HISTORY_RETENTION_DAYS_DEFAULT = 90
SMALL_CLAIM_AMOUNT_THRESHOLD_DEFAULT = 100_000
LARGE_CLAIM_AMOUNT_THRESHOLD_DEFAULT = 1_000_000
MULTIPLE_CLAIMS_DEFENDANT_THRESHOLD_DEFAULT = 3
MASS_ADDRESS_THRESHOLD_DEFAULT = 10
# ГИР БО financial-ratio thresholds, calibrated by inn-check-ru on 2022-2024 bankruptcies
# (references/kalibrovka.md there) - a per-flag estimate, not a verdict's accuracy.
EQUITY_RATIO_THRESHOLD_DEFAULT = 0.1
CURRENT_RATIO_THRESHOLD_DEFAULT = 1.0
REVENUE_DROP_THRESHOLD_DEFAULT = 0.5


class RuBusinessCheckSettings(Base):
    """Single-row configuration for the RU Business Check feature - flag-engine
    thresholds and history retention, both settings-backed (not hardcoded) so the
    analyst can tune them without a code change, pre-filled with the guide's own
    defaults."""

    __tablename__ = "ru_business_check_settings"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Singleton row id, always 1")
    fresh_registration_threshold_days: Mapped[int] = mapped_column(
        Integer,
        default=FRESH_REGISTRATION_THRESHOLD_DAYS_DEFAULT,
        comment="Registration age below which the soft 'fresh registration' flag fires",
    )
    history_retention_days: Mapped[int] = mapped_column(
        Integer,
        default=HISTORY_RETENTION_DAYS_DEFAULT,
        comment=(
            "Days a search (including its raw scraped payloads) is kept before "
            "automatic deletion; 0 = unlimited"
        ),
    )
    small_claim_amount_threshold: Mapped[int] = mapped_column(
        Integer,
        default=SMALL_CLAIM_AMOUNT_THRESHOLD_DEFAULT,
        comment=(
            "Claim amount (RUB) below which a single resolved arbitration case as "
            "defendant is a soft flag"
        ),
    )
    large_claim_amount_threshold: Mapped[int] = mapped_column(
        Integer,
        default=LARGE_CLAIM_AMOUNT_THRESHOLD_DEFAULT,
        comment=(
            "Claim amount (RUB) above which any arbitration case as defendant "
            "triggers the 'significant claims' soft flag"
        ),
    )
    multiple_claims_defendant_threshold: Mapped[int] = mapped_column(
        Integer,
        default=MULTIPLE_CLAIMS_DEFENDANT_THRESHOLD_DEFAULT,
        comment=(
            "Number of arbitration cases as defendant at/above which the 'multiple "
            "claims' soft flag fires"
        ),
    )
    mass_address_threshold: Mapped[int] = mapped_column(
        Integer,
        default=MASS_ADDRESS_THRESHOLD_DEFAULT,
        comment="Number of other entities registered at the same address (pb.nalog.ru) "
        "at/above which the 'mass registration address' soft flag fires",
    )
    equity_ratio_threshold: Mapped[float] = mapped_column(
        Float,
        default=EQUITY_RATIO_THRESHOLD_DEFAULT,
        comment="ГИР БО equity ratio (строка 1300 / строка 1600) below which the soft "
        "'low equity ratio' flag fires",
    )
    current_ratio_threshold: Mapped[float] = mapped_column(
        Float,
        default=CURRENT_RATIO_THRESHOLD_DEFAULT,
        comment="ГИР БО current ratio (строка 1200 / строка 1500) below which the soft "
        "'low current liquidity' flag fires",
    )
    revenue_drop_threshold: Mapped[float] = mapped_column(
        Float,
        default=REVENUE_DROP_THRESHOLD_DEFAULT,
        comment="Year-over-year ГИР БО revenue drop (0-1 fraction) above which the soft "
        "'revenue drop' flag fires",
    )
