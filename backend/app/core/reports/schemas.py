from dataclasses import dataclass, field


@dataclass
class ReportRow:
    """A single label/value line within a report section, already formatted for display.

    `href`, when set, renders `value` as a clickable link (both in the HTML output and in
    the PDF, since xhtml2pdf renders `<a href>` as a real clickable PDF link) - e.g. a
    deep link to the specific source request that produced this row, not just the source's
    general homepage.
    """

    label: str
    value: str
    href: str | None = None


@dataclass
class ReportSection:
    """A titled group of rows within a report.

    E.g. one service's result, or one email header block.
    """

    title: str
    rows: list[ReportRow] = field(default_factory=list)
