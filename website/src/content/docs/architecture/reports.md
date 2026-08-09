---
title: Reports & Exports
description: Generating HTML/PDF reports from lookups and analyses.
sidebar:
  order: 50
---

Several features can turn a result into a shareable report:

- **IOC Lookup** — any saved single-lookup history entry can be exported as an HTML or PDF
  report.
- **Email Analyzer** — export a report directly from an analysis result; since email analyses
  aren't persisted to history, this endpoint takes the result data itself rather than an ID.
- **Username Search** — maigret-sourced scans can export using Maigret's own report writers
  (HTML, PDF, and more); social-analyzer-sourced scans don't support export.
- **CVSS Calculator** — export a calculated score as Markdown or JSON.

Reports render in either English or Russian depending on the app's UI language setting.

PDF rendering runs entirely server-side (Jinja2 templates → `xhtml2pdf`) — no external service or
headless browser is involved for report generation itself.
