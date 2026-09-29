import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.features.ru_business_check.config.ru_business_check_config import (
    missing_required_sources as required_sources_not_checked,
)


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
    # Date only (DD.MM.YYYY) - to help an analyst rule out a same-name collision; the ЕГРЮЛ
    # extract carries no director birth date, so it can't be compared automatically.
    birth_date: str | None = None


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


class FedresursMessage(BaseModel):
    date: str
    type: str
    number: str | None = None
    role: str | None = None
    signal: str | None = None
    url: str | None = None


class FedresursSignal(BaseModel):
    code: str
    date: str
    type: str | None = None
    number: str | None = None
    url: str | None = None


class FedresursData(BaseModel):
    checked: bool = False
    found: bool = False
    status_text: str | None = None
    is_active_bankruptcy: bool = False
    # False when the status text is outside the live-observed vocabulary (reported as a
    # soft flag, never read as clean). Rows saved before this field existed default True.
    status_recognized: bool = True
    profile_url: str | None = None
    publications_checked: bool = False
    publications_total: int | None = None
    publications_truncated: bool = False
    publications_note: str | None = None
    messages: list[FedresursMessage] = Field(default_factory=list)
    signals: list[FedresursSignal] = Field(default_factory=list)


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


class GirBoYear(BaseModel):
    year: int
    reported_at: str | None = None
    revenue: float | None = None
    net_profit: float | None = None
    assets: float | None = None
    equity: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    long_term_liabilities: float | None = None
    cash: float | None = None
    # False when the period's detail form couldn't be fetched - only revenue/assets
    # (from the period list) are then filled.
    detail_loaded: bool = False


class GirBoData(BaseModel):
    checked: bool = False
    found: bool = False
    has_reports: bool = False
    org_name: str | None = None
    status_code: str | None = None
    profile_url: str | None = None
    unit: str = "тыс. руб."
    years: list[GirBoYear] = Field(default_factory=list)
    note: str | None = None


class MspData(BaseModel):
    checked: bool = False
    found: bool = False
    category_code: int | None = None
    category: str | None = None
    is_active: bool | None = None
    is_new: bool | None = None
    registered_at: str | None = None
    removed_at: str | None = None


class DisqualifiedDumpRecord(BaseModel):
    record_number: str
    full_name: str
    org_name: str | None = None
    org_inn: str | None = None
    position: str | None = None
    article: str | None = None
    term: str | None = None
    start_date: str
    end_date: str
    active: bool
    same_company: bool


class DisqualifiedDumpData(BaseModel):
    checked: bool = False
    dump_date: str | None = None
    valid_until: str | None = None
    outdated: bool = False
    director_confirmed: bool = False
    director_records: list[DisqualifiedDumpRecord] = Field(default_factory=list)
    company_records: list[DisqualifiedDumpRecord] = Field(default_factory=list)


class CbrWarningRecord(BaseModel):
    cbr_id: int
    name: str | None = None
    sign: str | None = None
    listed_at: str | None = None
    closed: bool = False
    comment: str | None = None
    is_clone: bool = False


class CbrWarningData(BaseModel):
    checked: bool = False
    # Set for an individual entrepreneur: the list only carries legal entities' ИНН.
    not_applicable: str | None = None
    as_of: str | None = None
    outdated: bool = False
    records: list[CbrWarningRecord] = Field(default_factory=list)


class OfacSdnRecord(BaseModel):
    ent_num: int
    name: str
    kind: str
    programs: str | None = None


class OfacSdnData(BaseModel):
    checked: bool = False
    as_of: str | None = None
    outdated: bool = False
    records: list[OfacSdnRecord] = Field(default_factory=list)


class ExtraData(BaseModel):
    """Sources stored in `extra_data` rather than a dedicated column pair (see
    docs/adr/0014-*.md); one optional key per source id."""

    gir_bo: GirBoData | None = None
    msp: MspData | None = None
    disqualified_dump: DisqualifiedDumpData | None = None
    cbr_warning: CbrWarningData | None = None
    ofac_sdn: OfacSdnData | None = None


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
    extra_data: ExtraData | None = None
    extra_raw: dict[str, str] | None = None
    raw_sha256: dict[str, str] | None = None
    flags: list[Flag] = Field(default_factory=list)
    checked_sources: list[str] = Field(default_factory=list)
    pending_sources: list[str] = Field(default_factory=list)
    candidates: list[Candidate] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def missing_required_sources(self) -> list[str]:
        """`REQUIRED_SOURCES` members this scan didn't check - why a verdict is
        `incomplete`. Served from here so the UI never keeps its own copy of the list."""
        if self.risk_level != "incomplete":
            return []
        return required_sources_not_checked(self.checked_sources)

    model_config = ConfigDict(from_attributes=True)
