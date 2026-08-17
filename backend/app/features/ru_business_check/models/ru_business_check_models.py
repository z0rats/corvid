import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class RuBusinessCheckSearch(Base):
    """A single RU Business Check due-diligence scan (ЕГРЮЛ + РДЛ + арбитраж, Stage 1-2)"""

    __tablename__ = "ru_business_check_searches"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    query: Mapped[str] = mapped_column(
        String(500), comment="Raw user input - ИНН or company/IP name"
    )
    resolved_inn: Mapped[str | None] = mapped_column(
        String(12),
        index=True,
        comment="Resolved ИНН, once the ЕГРЮЛ lookup matches a single entity",
    )
    entity_type: Mapped[str | None] = mapped_column(
        String(30), comment="'legal_entity' or 'individual_entrepreneur', once resolved"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="running", comment="running, completed, cancelled, or failed"
    )
    error: Mapped[str | None] = mapped_column(Text, comment="Error detail if status is failed")

    searched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="When the scan started"
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="When the scan reached a terminal state - the report's 'as of' date",
    )

    egrul_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "Parsed ЕГРЮЛ/ЕГРИП fields (name, address, director, founders, ОКВЭД, "
            "capital, registry status)"
        ),
    )
    egrul_raw: Mapped[str | None] = mapped_column(
        Text,
        comment=(
            "Verbatim ЕГРЮЛ payload (search-result JSON + extracted PDF text) as "
            "received from egrul.nalog.ru"
        ),
    )

    disqualification_result: Mapped[dict | None] = mapped_column(
        JSON, comment="РДЛ check result: {checked, matched, requires_manual_review, matches: [...]}"
    )
    disqualification_raw: Mapped[str | None] = mapped_column(
        Text, comment="Verbatim РДЛ payload as received from service.nalog.ru/disqualified.do"
    )

    arbitration_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "Arbitration case list: {checked, cases: [{case_number, "
            "date_registered, role, status, court, claim_amount, case_url}]}"
        ),
    )
    arbitration_raw: Mapped[str | None] = mapped_column(
        Text, comment="Verbatim arbitration search-result payload as received from kad.arbitr.ru"
    )

    fedresurs_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Bankruptcy check result: {checked, found, status_text, is_active_bankruptcy, "
        "profile_url}",
    )
    fedresurs_raw: Mapped[str | None] = mapped_column(
        Text, comment="Verbatim bankruptcy search-result payload as received from fedresurs.ru"
    )

    pb_nalog_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Прозрачный бизнес result: {checked, found, mass_address_count, "
        "mass_address_companies, profile_url}",
    )
    pb_nalog_raw: Mapped[str | None] = mapped_column(
        Text, comment="Verbatim search+detail payload as received from pb.nalog.ru"
    )

    fedsfm_result: Mapped[dict | None] = mapped_column(
        JSON,
        comment="ФедСФМ (терроризм/финансирование ОМУ) check result: {checked, matched, "
        "requires_manual_review, matches: [...]}",
    )
    fedsfm_raw: Mapped[str | None] = mapped_column(
        Text, comment="Verbatim ФедСФМ payload as received from fedsfm.ru/TerroristSearch"
    )

    website: Mapped[str | None] = mapped_column(
        String(255),
        comment="Optional company website, user-supplied - display-only, not analyzed by "
        "this feature itself; the UI links it out to domain_finder's own WHOIS/DNS/CT "
        "analysis instead of duplicating it here",
    )

    rnp_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment="РНП (реестр недобросовестных поставщиков) check result: {checked, "
        "entries: [{registry_number, law, name, inn, included_date, updated_date, "
        "planned_exclusion_date, status, eruz_number, detail_url}]}",
    )
    rnp_raw: Mapped[str | None] = mapped_column(
        Text, comment="Verbatim RSS payload as received from zakupki.gov.ru"
    )

    flags: Mapped[list | None] = mapped_column(
        JSON, comment="List of {code, severity, title, detail} risk flags"
    )
    risk_level: Mapped[str | None] = mapped_column(
        String(10),
        comment=(
            "low, medium, or high - based only on checked_sources, never implies "
            "full-methodology coverage"
        ),
    )

    checked_sources: Mapped[list | None] = mapped_column(
        JSON, comment="Source keys actually queried this scan, snapshotted at scan time"
    )
    pending_sources: Mapped[list | None] = mapped_column(
        JSON, comment="Source keys not yet available this stage, snapshotted at scan time"
    )

    candidates: Mapped[list | None] = mapped_column(
        JSON,
        comment=(
            "Brief per-entity info when the query matched multiple ЕГРЮЛ/ЕГРИП rows "
            "(name search) - empty once resolved to a single entity"
        ),
    )
