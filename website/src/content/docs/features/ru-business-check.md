---
title: RU Business Check
description: Due-diligence check on a Russian legal entity or sole proprietor by ИНН/name, across official registries and published lists.
sidebar:
  order: 150
---

Collapses the manual "check a Russian counterparty" workflow — normally 30–40 minutes across
several official registries — into a single ИНН or company/IP name query. No API keys.

The in-app interface and generated reports are Russian-only by design, since the sources are
Russian registries and their output is inherently in Russian.

## What it checks

Live lookups (each result keeps the source's raw payload, with a SHA-256 recorded when it was
captured, for independent verification):

- **ЕГРЮЛ/ЕГРИП extract** — name, ОГРН/ИНН/КПП, registration date, address, director, founders,
  ОКВЭД, capital, from `egrul.nalog.ru`.
- **Bankruptcy (Федресурс)** — an active bankruptcy stage is a hard flag; an unrecognized status
  text is a soft "check manually" flag (never read as clean). For legal entities, the latest
  publications add soft signals: creditor's or debtor's intent to file for bankruptcy, a
  liquidation decision, a "недостоверность сведений" notice, a reorganization in the last year.
  A message only counts when the company is its *subject* — a bank that publishes hundreds of
  creditor notices about other companies isn't flagged for them.
- **РНП** (`zakupki.gov.ru`) — an active record for the exact ИНН is a hard flag.
- **Disqualified persons (РДЛ)** — the director's ФИО against the online registry; a name-only
  match is always a soft "check manually" flag, with the registry's birth date shown to help.
- **Arbitration cases** (`kad.arbitr.ru`) — case history as plaintiff/defendant, soft flags only.
  This site often refuses automated access from outside Russia; the check then reports "not
  checked" rather than an empty history.
- **Прозрачный бизнес** — mass-registration-address indicator, soft flag.
- **ФедСФМ** — the director against the terrorism/WMD-financing list, soft flag (name-only).
- **Financial statements (ГИР БО)** — revenue, profit, balance for the last 3 years. Soft flags
  for a low equity ratio, low current liquidity and a sharp revenue drop (thresholds in
  Settings). Banks, insurers and sole proprietors have no statements there — shown as such.
- **МСП register** — whether it's a registered micro/small/medium business (informational).

Local copies of published lists, refreshed in the background and matched by exact ИНН — the ИНН
is never sent to a third party, and the checks work when the source site is slow:

- **ФНС disqualified-persons register** (weekly) — a record matching the director's ФИО **and**
  this company's ИНН, in force today, is a *hard* flag; other in-force records of the company's
  officers are a soft signal. Birth dates and places are not stored.
- **Банк России warning list** (every 2 days) — soft flag, worded as the regulator's statement
  ("signs of illegal activity"), not a court finding. Entries that misuse a legitimate firm's
  data are shown but never counted against the ИНН owner.
- **OFAC SDN list** (every 2 days) — a match on the ИНН is a hard flag, worded as a US-list status.
  **No match is not proof of no sanctions**: OFAC records an ИНН for only part of its Russian
  entries (some large banks are listed without one), and the EU list isn't checked.

Until a list has been downloaded for the first time (right after install), its check shows as
"not checked".

## How the verdict works

- **Hard flags** (confirmed disqualification, active bankruptcy, РНП, OFAC match) make the level
  **High**. Soft flags raise it to **Medium**; three *independent sources* with soft flags make it
  **High**.
- **"Проверка неполная"** — if ЕГРЮЛ, Федресурс or РНП couldn't be checked and no hard flag was
  found, the level is *incomplete*, not Low: the missing check could have found one. The result
  always lists which sources were checked and which weren't.
- A source that fails or whose site changed its format is reported as not checked, never as
  "nothing found".
- ФССП (enforcement proceedings) isn't automated — its search demands a CAPTCHA on every query, so
  the result offers a manual-check link.

Results are saved to a searchable history (retention configurable in **Settings → RU Business
Check**), repeat lookups within 24 hours reuse the saved result unless refreshed, and any result
exports as an HTML or PDF report with per-source links and the payload fingerprints.
