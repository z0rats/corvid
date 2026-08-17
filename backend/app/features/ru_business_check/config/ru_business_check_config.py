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
]
PLANNED_SOURCES: list[str] = ["fssp"]

SOURCE_LABELS: dict[str, str] = {
    "egrul": "ЕГРЮЛ/ЕГРИП",
    "disqualified_persons": "Реестр дисквалифицированных лиц (РДЛ)",
    "arbitration": "Арбитражные дела",
    "fssp": "Исполнительные производства (ФССП)",
    "fedresurs": "Банкротство (Федресурс)",
    "pb_nalog": "Прозрачный бизнес (ФНС)",
    "fedsfm": "Перечень терроризм/ОМУ (ФедСФМ)",
    "zakupki_rnp": "Реестр недобросовестных поставщиков (РНП)",
}

# Wall-clock ceiling for one full scan (ЕГРЮЛ search + PDF generation/poll + РДЛ lookup +
# pb.nalog.ru's own two two-step async job flows) - egrul.nalog.ru's own PDF generation
# step and pb.nalog.ru's search/detail polling can each take several seconds, so this is
# generous compared to a single HTTP request timeout.
WALL_CLOCK_TIMEOUT_SECONDS = 150
