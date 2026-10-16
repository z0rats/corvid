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

Each template runs against the model picked in its own form, which lists every model currently
available, local Ollama models included. If none is picked, or the picked one is no longer
available (its key was removed, Ollama stopped), it falls back to the model configured for AI
templates under [AI Settings](/corvid/getting-started/settings-reference/#ai-settings) (the
`llm_templates_model` override, or the default model). See
[AI / LLM Providers](/corvid/architecture/ai-providers/) for setup.
