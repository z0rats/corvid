import datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, String, Text
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

    extra_data: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "Parsed results of sources added after the dedicated *_data columns, keyed by "
            "source id (e.g. {gir_bo: {...}}) - new sources land here instead of costing "
            "two columns and a migration each, see docs/adr/0014-*.md"
        ),
    )
    extra_raw: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Verbatim payloads for extra_data's sources, keyed the same way: {source: text}",
    )

    raw_sha256: Mapped[dict | None] = mapped_column(
        JSON,
        comment=(
            "SHA-256 of each source's verbatim payload as captured at scan time, keyed by "
            "source id: {source: hex digest}; sources with no payload are omitted"
        ),
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


class DisqualifiedRecord(Base):
    """One row of the ФНС open-data disqualified-persons register (data.nalog.ru), kept
    locally so a scan can match a director by ФИО *and* the organization's ИНН - a second
    identifier the online search doesn't return. The birth date and place of birth, the
    judge and the raw CSV are deliberately not stored. Replaced wholesale on each refresh."""

    __tablename__ = "ru_business_check_disqualified_records"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    record_number: Mapped[str] = mapped_column(
        String(20), comment="Register record number (CSV column G1)"
    )
    full_name: Mapped[str] = mapped_column(
        String(300),
        index=True,
        comment="ФИО normalized for matching: upper case, ё->е, single spaces (column G2)",
    )
    org_name: Mapped[str | None] = mapped_column(
        String(500), comment="Organization the person was disqualified in (column G5)"
    )
    org_inn: Mapped[str | None] = mapped_column(
        String(12),
        index=True,
        comment="That organization's ИНН (column G6) - only ~36% of records carry it",
    )
    position: Mapped[str | None] = mapped_column(String(300), comment="Position held (column G7)")
    article: Mapped[str | None] = mapped_column(String(300), comment="КоАП article (column G8)")
    term: Mapped[str | None] = mapped_column(
        String(50), comment="Disqualification term as written, e.g. '2 г 0 м 0 д' (column G12)"
    )
    start_date: Mapped[datetime.date] = mapped_column(
        Date, comment="Disqualification start (column G13)"
    )
    end_date: Mapped[datetime.date] = mapped_column(
        Date, comment="Disqualification end (column G14)"
    )


class CbrWarningRecord(Base):
    """One entry of the Банк России "list of companies with signs of illegal activity in the
    financial market" that carries an ИНН (~11% of the ~27k entries; the rest are websites and
    "points of presence" without one), kept locally so a scan matches by exact ИНН without
    sending it to the regulator. Replaced wholesale on each refresh."""

    __tablename__ = "ru_business_check_cbr_warning_records"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    cbr_id: Mapped[int] = mapped_column(Integer, comment="The list's own entry id (`Id`)")
    inn: Mapped[str] = mapped_column(
        String(10), index=True, comment="10-digit ИНН of the listed legal entity"
    )
    name: Mapped[str | None] = mapped_column(String(500), comment="Listed name (`Name`)")
    sign: Mapped[str | None] = mapped_column(
        String(500), comment="The regulator's stated sign of illegal activity (`Sign`)"
    )
    listed_at: Mapped[datetime.date | None] = mapped_column(
        Date, comment="Date the entry was added to the list (`DT`)"
    )
    closed: Mapped[bool] = mapped_column(
        Boolean, comment="The regulator marks the organization as liquidated (`Closed`)"
    )
    comment: Mapped[str | None] = mapped_column(String(1000), comment="Regulator's note")
    is_clone: Mapped[bool] = mapped_column(
        Boolean,
        comment="Note says the entry misuses a legitimate market participant's data: the ИНН "
        "owner is the impersonated party, not the offender",
    )


class OfacSdnRecord(Base):
    """One (SDN entry, Russian ИНН) pair from the US Treasury OFAC SDN list. Only entries
    whose remarks carry a `Tax ID No. <ИНН> (Russia)` are kept (~3.7k of ~19k), so a scan
    matches by exact ИНН - no name matching, no transliteration - without sending the ИНН
    anywhere. Replaced wholesale on each refresh."""

    __tablename__ = "ru_business_check_ofac_sdn_records"

    id: Mapped[int] = mapped_column(primary_key=True, comment="Surrogate primary key")
    ent_num: Mapped[int] = mapped_column(Integer, comment="The SDN list's own entry number")
    inn: Mapped[str] = mapped_column(
        String(12),
        index=True,
        comment="Russian ИНН from the entry's remarks (10 digits = legal entity, 12 = person)",
    )
    name: Mapped[str] = mapped_column(String(500), comment="SDN name (transliterated)")
    kind: Mapped[str] = mapped_column(String(20), comment="'entity' (SDN type -0-) or 'individual'")
    programs: Mapped[str | None] = mapped_column(
        String(500), comment="Sanctions programs, e.g. 'UKRAINE-EO13661] [RUSSIA-EO14024'"
    )
