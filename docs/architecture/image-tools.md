# `backend/app/features/image_tools/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

## EXIF/metadata extraction

Primary pass via `exifread`+Pillow. An optional richer pass runs through the `exiftool` binary
(`exiftool_service.py`) — the image is piped over stdin rather than written to a temp file, and a
few filesystem-level tags (which would describe the anonymous pipe, not the uploaded file) are
filtered out of the result. Gracefully returns `None` if the binary isn't installed; installed
version is surfaced at `/api/image/health` with no PyPI-style update-check, since it's
apt-installed at image-build time, not a pip package (see AGENTS.md's Conventions section for
this pattern generally, shared with `subfinder`/`httpx` in `domain_finder`).

Also provides hashing and keyless reverse-image-search deep-links (no API key needed).

## AI photo-geolocation (`POST /api/image/geolocate`)

`image_geolocation_service.py` reuses `llm_service.py`'s multimodal support
(`execute_structured_prompt`'s `image_data`/`image_media_type`) to produce a geolocation
hypothesis — the module's only feature needing an LLM key or an
`ai_settings.image_geolocation_model` override. Each run is persisted
(`geolocation_history_*`); the full response JSON is stored, so new response fields need no migration.

The model also returns `visible_text` (a verbatim transcription; no OCR dependency).
`text_signals_service.compute_text_signals` turns it into `text_signals` — scripts, non-Western
digits, language-specific letters, currency marks, ccTLDs, calling codes (prefixes shared by
more than two countries are dropped) and regional words — by lookup in `image_tools/lookup_data/`
(`text_signals.json`, `country_info.json`, provenance in `lookup_data/NOTICE.md`; derived from GeoInt).
Then, if a top-3 candidate (or a specific text signal, at most 3 countries) names a country with a
row in `country_clues.json`, `image_geolocation_service._cross_check` runs a second model call with
the photo, the first-pass JSON, the text signals and only those rows (`geo_clues_service.py`), so
the prompt stays small for local models with short context windows. Any failure keeps the
first-pass result; the first pass's `visible_text` is always kept; `reference_countries` records
what was checked. This doubles the LLM calls for a recognised-country run.
These are computed server-side, never model output, hence `ImageGeolocationAnalysis` (history
detail shape) extends the model-facing `ImageGeolocationAIResult`.

## GPS chapter (`GpsMap.jsx`)

Deep-links a photo's coordinates into a few keyless external geo tools (`GEO_EXTERNAL_TOOLS` in
`imageConstants.js`) and, if an optional `google_maps` key is configured, embeds a live Street
View panorama. This is the one API key in this app whose raw value is exposed to the frontend
rather than proxied server-side, since Google's Maps Embed API is consumed client-side by design
— see `docs/adr/0008-google-maps-key-exposed-to-frontend.md`.

## ChronoVerify (`POST /api/image/chronoverify`)

Opt-in provenance check: sends the image to `chronoverify.com` only on an explicit click (never
automatically, unlike this module's local checks), via `chronoverify_service.py`, for a
C2PA-provenance/pixel-forensics verdict. Keyless (free, rate-limited) or with an optional
`chronoverify` key for higher limits.
