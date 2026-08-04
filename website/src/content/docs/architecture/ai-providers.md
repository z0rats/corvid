---
title: AI / LLM Providers
description: Configuring Anthropic, Google, OpenAI, or a local Ollama server for AI features.
---

Several features are AI-assisted and optional: newsfeed article analysis and report generation,
email analysis, AI prompt templates, and photo geolocation. None of the rest of the app depends
on an LLM being configured — these features simply won't produce AI output without one.

## Supported providers

- **Anthropic**, **Google**, **OpenAI** — add the corresponding API key under
  **Settings → API Keys** to make that provider's models available.
- **Local Ollama** — set `LLM_OLLAMA_BASE_URL` to a running Ollama server's OpenAI-compatible
  endpoint (e.g. `http://host.docker.internal:11434/v1` to reach a host-run Ollama from inside
  the container). No API key needed. Any model already pulled into that Ollama server is
  auto-discovered and shows up alongside the cloud providers. If the server is unreachable, it's
  silently skipped rather than failing startup.

## Choosing models

Once at least one provider is configured, pick models under
[Settings → AI Settings](/corvid/getting-started/settings-reference/#ai-settings): a default
model used as a fallback, plus optional per-feature overrides for newsfeed analysis, newsfeed
reports, email analysis, AI templates, and photo geolocation.

## Multimodal use

Photo geolocation ([Image Tools](/corvid/features/image-tools/)) sends the uploaded image
directly to the configured model — pick a model with vision support for that feature to produce
useful output.
