---
title: Email Analyzer
description: .eml parsing, header checks, and AI-assisted analysis.
sidebar:
  order: 30
---

Drag and drop an `.eml` file to parse it: headers, a battery of security checks, and IOC
extraction all run automatically. Checks include SPF/DKIM/DMARC authentication results,
From/Reply-To/Return-Path mismatches, homograph (lookalike-domain) attacks, spoofed or suspicious
attachment extensions, suspicious HTML content (redirects, IP-literal URLs, data URIs, encoded
URLs), mail-relay chain analysis, and date/mailer anomalies. Extracted IOCs can be pushed straight
into [IOC Tools](/corvid/features/ioc-tools/) for further lookup against threat-intel services.

AI-assisted analysis is optional — configure a model under
[AI Settings](/corvid/getting-started/settings-reference/#ai-settings) (the `email_analyzer_model`
override, or the default model) to get a written read on the message alongside the mechanical
checks.

Unlike IOC Lookup, analyses here aren't persisted to history — export a report directly from an
analysis result instead (see [Reports & Exports](/corvid/architecture/reports/)).
