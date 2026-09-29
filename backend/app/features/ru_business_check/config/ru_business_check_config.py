# Tunables for the ru_business_check feature. Which sources exist at this stage is a
# fixed pipeline constant (not a settings-backed choice) - hardcoded thresholds live in
# core/settings/ru_business_check instead, since those are genuinely worth tuning per
# deployment while the pipeline shape itself isn't.

FEATURE_NAME = "ru_business_check"

# Sources this stage actually queries, vs. the ones still planned. `fssp` stays planned
# permanently rather than becoming available - its official API is dead and its public
# web search demands solving a CAPTCHA on every single query (live-confirmed, not just an
# abuse-triggered block like arbitration's/fedresurs' anti-bot layers), so per
# docs/adr/0006-*.md's never-bypass-CAPTCHA policy it isn't automatable at all; the
# frontend instead offers a manual deep link to fssp.gov.ru wherever it shows up as
# pending. Snapshotted onto each search row at scan time (see models) so an earlier-stage
# history row keeps showing the coverage that was true when it ran, even after these lists
# change.
AVAILABLE_SOURCES: list[str] = [
    "egrul",
    "disqualified_persons",
    "arbitration",
    "fedresurs",
    "pb_nalog",
    "fedsfm",
    "zakupki_rnp",
    "gir_bo",
    "msp",
    "disqualified_dump",
    "ofac_sdn",
    "cbr_warning",
]
PLANNED_SOURCES: list[str] = ["fssp"]

# Sources whose *absence* makes a "low"/"medium" verdict unsafe to show: they are the ones
# that can raise a hard flag (ИНН-precise), so a scan where one failed cannot claim the
# hard-flag conditions were ruled out. `flag_engine` turns such a verdict into
# "incomplete" instead. Soft-only sources (арбитраж, online РДЛ, ФедСФМ, Прозрачный бизнес,
# ГИР БО, ЦБ list) and the informational МСП are not listed - their failure is still visible
# via `pending_sources`, but doesn't invalidate a verdict that only ever moves on hard flags.
# The locally cached dumps that *can* raise a hard flag (ФНС disqualified register, OFAC SDN)
# aren't required either: they are populated in the background after install/first start, so
# requiring them would make every verdict `incomplete` until the first download; until then
# they show as "not checked" (pending). See docs/adr/0014-*.md.
REQUIRED_SOURCES: frozenset[str] = frozenset({"egrul", "fedresurs", "zakupki_rnp"})


def not_applicable_sources(extra_data: dict | None) -> list[str]:
    """Sources that don't apply to this entity (e.g. the ЦБ list for an ИП) - recorded in
    `extra_data` with a `not_applicable` explanation, and in neither `checked_sources` nor
    `pending_sources`."""
    return [
        key
        for key, result in (extra_data or {}).items()
        if isinstance(result, dict) and result.get("not_applicable")
    ]


def missing_required_sources(checked_sources: list[str] | None) -> list[str]:
    """`REQUIRED_SOURCES` members not in `checked_sources`, in `AVAILABLE_SOURCES` order -
    what makes a verdict `incomplete` (shared by the API schema and the export)."""
    checked = set(checked_sources or [])
    return [s for s in AVAILABLE_SOURCES if s in REQUIRED_SOURCES and s not in checked]


SOURCE_LABELS: dict[str, str] = {
    "egrul": "ЕГРЮЛ/ЕГРИП",
    "disqualified_persons": "Реестр дисквалифицированных лиц (РДЛ)",
    "arbitration": "Арбитражные дела",
    "fssp": "Исполнительные производства (ФССП)",
    "fedresurs": "Банкротство (Федресурс)",
    "pb_nalog": "Прозрачный бизнес (ФНС)",
    "fedsfm": "Перечень терроризм/ОМУ (ФедСФМ)",
    "zakupki_rnp": "Реестр недобросовестных поставщиков (РНП)",
    "gir_bo": "Бухгалтерская отчётность (ГИР БО)",
    "msp": "Реестр МСП",
    "disqualified_dump": "Реестр дисквалифицированных лиц (выгрузка ФНС)",
    "cbr_warning": "Список ЦБ: признаки нелегальной деятельности",
    "ofac_sdn": "Санкционный список OFAC SDN (США)",
}

# Wall-clock ceiling for one full scan (ЕГРЮЛ search + PDF generation/poll + РДЛ lookup +
# pb.nalog.ru's own two two-step async job flows) - egrul.nalog.ru's own PDF generation
# step and pb.nalog.ru's search/detail polling can each take several seconds, so this is
# generous compared to a single HTTP request timeout.
WALL_CLOCK_TIMEOUT_SECONDS = 150
