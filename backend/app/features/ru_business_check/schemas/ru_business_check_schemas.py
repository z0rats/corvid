import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScanRequest(BaseModel):
    """Request to run a RU Business Check scan (ЕГРЮЛ + РДЛ + арбитраж)"""

    query: str = Field(
        ..., min_length=1, max_length=500, description="ИНН (приоритетно) или название юрлица/ИП"
    )
    force_refresh: bool = Field(
        default=False,
        description=(
            "Игнорировать кэш и запросить источники заново, даже если есть свежий "
            "результат по этому запросу"
        ),
    )
    website: str | None = Field(
        default=None,
        max_length=255,
        description="Сайт компании (опционально) — сохраняется вместе с проверкой и "
        "выводится ссылкой в IOC-инструменты (WHOIS/DNS/CT), не анализируется здесь",
    )


class Founder(BaseModel):
    name: str
    share: str | None = None


class EgrulData(BaseModel):
    full_name: str | None = None
    short_name: str | None = None
    ogrn: str | None = None
    inn: str | None = None
    kpp: str | None = None
    registration_date: datetime.date | None = None
    address: str | None = None
    director_name: str | None = None
    director_position: str | None = None
    founders: list[Founder] = Field(default_factory=list)
    okved_main: str | None = None
    okved_additional: list[str] = Field(default_factory=list)
    capital: str | None = None
    registry_status: str | None = None


class DisqualificationMatch(BaseModel):
    full_name: str
    record_number: str | None = None
    organization: str | None = None
    position: str | None = None
    article: str | None = None
    issuing_authority: str | None = None
    judge: str | None = None
    details: str | None = None


class DisqualificationResult(BaseModel):
    checked: bool = False
    matched: bool = False
    requires_manual_review: bool = False
    matches: list[DisqualificationMatch] = Field(default_factory=list)


class ArbitrationCase(BaseModel):
    case_number: str
    date_registered: str | None = None
    role: Literal["plaintiff", "defendant", "other"] = "other"
    status: str | None = None
    court: str | None = None
    claim_amount: float | None = None
    case_url: str | None = None


class ArbitrationData(BaseModel):
    checked: bool = False
    cases: list[ArbitrationCase] = Field(default_factory=list)


class FedresursData(BaseModel):
    checked: bool = False
    found: bool = False
    status_text: str | None = None
    is_active_bankruptcy: bool = False
    profile_url: str | None = None


class MassAddressCompany(BaseModel):
    inn: str | None = None
    name: str | None = None


class PbNalogData(BaseModel):
    checked: bool = False
    found: bool = False
    mass_address_count: int = 0
    mass_address_companies: list[MassAddressCompany] = Field(default_factory=list)
    profile_url: str | None = None


class FedsfmMatch(BaseModel):
    id: str | None = None
    full_name: str
    terrorist_type: str | None = None
    status: str | None = None


class FedsfmResult(BaseModel):
    checked: bool = False
    matched: bool = False
    requires_manual_review: bool = False
    matches: list[FedsfmMatch] = Field(default_factory=list)


class RnpEntry(BaseModel):
    registry_number: str | None = None
    law: str | None = None
    name: str | None = None
    inn: str | None = None
    included_date: str | None = None
    updated_date: str | None = None
    planned_exclusion_date: str | None = None
    status: str | None = None
    eruz_number: str | None = None
    detail_url: str | None = None


class RnpData(BaseModel):
    checked: bool = False
    entries: list[RnpEntry] = Field(default_factory=list)


class Candidate(BaseModel):
    """Brief info for one of several ЕГРЮЛ/ЕГРИП matches, when a name search was
    ambiguous - lets the frontend offer a disambiguation list instead of a dead end."""

    name: str | None = None
    inn: str | None = None
    ogrn: str | None = None
    address: str | None = None
    status: str | None = None


class Flag(BaseModel):
    code: str
    severity: Literal["hard", "soft"]
    title: str
    detail: str


class SearchSummary(BaseModel):
    """Summary of a past search, without raw source payloads"""

    id: int
    query: str
    resolved_inn: str | None = None
    entity_type: str | None = None
    status: str
    risk_level: str | None = None
    searched_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    """Full detail of a past search, including parsed data, flags, and raw source payloads"""

    error: str | None = None
    egrul_data: EgrulData | None = None
    egrul_raw: str | None = None
    disqualification_result: DisqualificationResult | None = None
    disqualification_raw: str | None = None
    arbitration_data: ArbitrationData | None = None
    arbitration_raw: str | None = None
    fedresurs_data: FedresursData | None = None
    fedresurs_raw: str | None = None
    pb_nalog_data: PbNalogData | None = None
    pb_nalog_raw: str | None = None
    fedsfm_result: FedsfmResult | None = None
    fedsfm_raw: str | None = None
    website: str | None = None
    rnp_data: RnpData | None = None
    rnp_raw: str | None = None
    flags: list[Flag] = Field(default_factory=list)
    checked_sources: list[str] = Field(default_factory=list)
    pending_sources: list[str] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
