---
title: Image Tools
description: EXIF/metadata extraction, hashing, reverse image search, and AI geolocation.
sidebar:
  order: 40
---

Upload an image to see every piece of metadata it carries — EXIF camera/device info, capture
timestamp, GPS location with a map link, embedded thumbnail, file properties, and
MD5/SHA1/SHA256 hashes. If the `exiftool` binary is available on the server, a second
"Exiftool (Extended)" section adds maker-note, XMP, and IPTC tags the primary EXIF parser
doesn't cover — purely supplementary, so its absence never affects the rest of the analysis.

Reverse image search works without any API keys: deep-link straight into Google Lens, Yandex,
Bing, and TinEye, either by URL or by using the same buttons to open each engine for a manual
upload.

When a photo carries GPS coordinates, the GPS chapter also links straight into a few other
keyless geo tools centered on that point: ShadowMap (shadow simulation), Flightradar24, and
Open Infrastructure Map. MapChecking has no coordinate-based deep link, so its button opens the
plain tool instead. If a Google Maps key is configured under Settings → API Keys, the same
chapter also embeds a live Street View panorama at those coordinates (no imagery everywhere —
Google shows its own "no coverage" message when none exists for a spot).

## AI photo geolocation

Optional, and the only other part of this module that needs an LLM — an OpenAI or Anthropic key, or a local Ollama model (no key needed); see
[AI / LLM Providers](/corvid/architecture/ai-providers/). Sends the uploaded image to the
configured model (`image_geolocation_model` override, or the default) and returns a geolocation
hypothesis. Pick a vision-capable model for useful results; models pulled into a local Ollama
server work too if they accept images. Each analysis is saved to a history list with HTML/PDF
report export.

The model also transcribes any legible text in the photo (signs, plates, phone numbers, prices).
Corvid then checks that transcription itself against lookup tables, so the "Hints from visible
text" panel is deterministic rather than model opinion: the script (Thai, Cyrillic, Hangul…),
non-Western digits, letters unique to a language (ł, ő, ї…), currency marks, country-code domains
(`.br`), international phone prefixes, and regional shop/street words (`talho`, `strasse`). These
narrow languages and plausible countries, not borders — minorities, tourists and imported goods
carry text abroad — and a transcription error produces a wrong hint, so check the photo.

When the first pass names a country that Corvid has reference notes for (driving side, plate
format, road paint, script, other strong tells), a second model call re-examines the photo against
those notes for the top candidates and the text hints, and the panel shows which countries were
cross-checked. This means a recognised-country analysis makes two model calls instead of one; if
the second call fails, the first result is kept. The notes are general knowledge about typical
conventions, not proof.

Lookup data derives from [GeoInt](https://github.com/marouane53/GeoINT) and
[geo-sleuth](https://github.com/Oldcircle/geo-sleuth) (both MIT), with country facts from
GeoNames (CC BY 4.0).

## ChronoVerify provenance check

Optional and opt-in — unlike every other chapter in this module, it does not run automatically
on upload; a "Check with ChronoVerify" button sends the image to
[chronoverify.com](https://chronoverify.com), a third-party service, only when clicked. Returns
one of five verdicts (`provenance_confirmed`, `consistent`, `metadata_anomaly`,
`manipulation_indicated`, `inconclusive`) with a confidence score, based on validating C2PA
Content Credentials against the official trust list, EXIF/XMP capture metadata, and
pixel-forensic signals (error-level analysis, noise dispersion). Works keyless (free, rate-limited
per IP); an optional key under Settings → API Keys raises the limit. Investigative triage, not
proof of tampering or authenticity — a clean verdict confirms provenance is intact, not that the
scene in the photo is true.
