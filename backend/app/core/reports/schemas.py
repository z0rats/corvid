from dataclasses import dataclass, field


@dataclass
class ReportRow:
    """A single label/value line within a report section, already formatted for display."""

    label: str
    value: str


@dataclass
class ReportSection:
    """A titled group of rows within a report (e.g. one service's result, one email header block)."""

    title: str
    rows: list[ReportRow] = field(default_factory=list)
