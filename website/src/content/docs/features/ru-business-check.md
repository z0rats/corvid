---
title: RU Business Check
description: Due-diligence check on a Russian legal entity or sole proprietor by ИНН/name.
sidebar:
  order: 150
---

Collapses the manual "check a Russian counterparty" workflow — normally 30–40 minutes across
several official government registries — into a single ИНН or company/IP name query.

The in-app interface and generated reports are Russian-only by design, since every source this
feature queries is a Russian government registry and its output is inherently in Russian.

## Stage 1

- **ЕГРЮЛ/ЕГРИП extract** — company/individual-entrepreneur registration data (name, ОГРН/ИНН/КПП,
  registration date, address, director, founders, ОКВЭД codes, capital), scraped from the
  official `egrul.nalog.ru` registry service (no API, no key required).
- **Disqualified-persons registry (РДЛ)** — checks the resolved director's full name against
  `service.nalog.ru`'s disqualified-persons registry. A name-only match is always surfaced as
  requiring manual review, never as an automatically confirmed fact — the registry gives no
  disambiguating identifier beyond full name, so a same-name collision is a real risk.

## Stage 2 (current)

- **Arbitration case history** — arbitration cases involving the resolved ИНН, from
  `kad.arbitr.ru`'s public case registry ("Картотека арбитражных дел"), including case status,
  court, role (plaintiff/defendant), claim amount where available, and a direct link to each
  case. Only soft flags fire from arbitration data (a single small resolved case as defendant,
  or several/large-value cases as defendant) — the checklist this feature is built from never
  puts arbitration in the automatic-high-risk tier on its own.

**Risk-flag engine** — hard/soft flags computed only from whichever sources are checked so far
(confirmed disqualification is the only hard flag right now; everything else is soft). The
result always states which sources were checked and which weren't — a risk verdict never implies
more than what was actually checked, since ФССП and Федресурс (Stage 3) aren't wired up yet.

Results (including each source's raw scraped payload, for independent verification) are saved to
a searchable history with a configurable retention period — see **Settings → RU Business Check**.

## Planned (later stages)

Enforcement proceedings (ФССП) and bankruptcy/pledge filings (Федресурс) — each its own stage,
since neither has an official API and needs its own scraper.
