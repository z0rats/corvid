---
title: Image Tools
description: EXIF/metadata extraction, hashing, reverse image search, and AI geolocation.
sidebar:
  order: 40
---

Upload an image to see every piece of metadata it carries — EXIF camera/device info, capture
timestamp, GPS location with a map link, embedded thumbnail, file properties, and
MD5/SHA1/SHA256 hashes.

Reverse image search works without any API keys: deep-link straight into Google Lens, Yandex,
Bing, and TinEye, either by URL or by using the same buttons to open each engine for a manual
upload.

## AI photo geolocation

Optional, and the only part of this module that needs an LLM key — see
[AI / LLM Providers](/corvid/architecture/ai-providers/). Sends the uploaded image to the
configured model (`image_geolocation_model` override, or the default) and returns a geolocation
hypothesis. Pick a vision-capable model for useful results. Like the rest of the module, nothing
here is persisted to history — it's a one-shot analysis.
