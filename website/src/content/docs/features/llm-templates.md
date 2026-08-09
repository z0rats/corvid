---
title: LLM Templates
description: User-defined AI prompt templates for analysis tasks.
sidebar:
  order: 110
---

Create reusable AI prompt templates, organized into categories, for tasks like log data analysis,
email text analysis, and source-code explanation. Templates support the prompt-engineering
workflow rather than hardcoding one fixed prompt per task — write, tweak, and re-run a prompt
against different input without losing earlier iterations.

Templates run against whichever model is configured for AI templates under
[AI Settings](/corvid/getting-started/settings-reference/#ai-settings) (the
`llm_templates_model` override, or the default model) — see
[AI / LLM Providers](/corvid/architecture/ai-providers/) for setup.
