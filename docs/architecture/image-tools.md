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
`ai_settings.image_geolocation_model` override. Stateless like the rest of this module (no
history persisted).

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
