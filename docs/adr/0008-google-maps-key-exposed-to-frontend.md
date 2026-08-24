# Expose the Google Maps key to the frontend, unlike every other API key

Every other key in `apikeys` is read server-side only: a feature's service layer fetches the
decrypted value and uses it in an outbound `httpx` call, so the raw value never reaches the
browser (see [0003](0003-encrypt-only-third-party-api-keys.md) for the storage-side rationale).
The optional `google_maps` key (Image Analyzer's embedded Street View panorama, `GpsMap.jsx`)
breaks that pattern: Google's Maps Embed API is designed to be consumed directly by the browser
as an iframe `src` query parameter (`/maps/embed/v1/streetview?key=...&location=...`) — there's
no server-side call to proxy, since the browser has to load the iframe itself. Google's own
mitigation for this is HTTP-referrer restriction on the key in Google Cloud Console, not secrecy.

Rather than either skipping the feature or inventing a general "read any key's raw value"
endpoint (which would turn one narrow, deliberate exception into a standing risk for every other
key in the table), `image_tools` gets one narrow route scoped to this single purpose:
`GET /api/image/street-view-key` (`google_maps_service.py`) returns just this one key's value,
gated behind the same single bearer access token every other `/api/*` route already requires —
no new trust boundary, since anyone with that token already has full access to the app and could
read the key by adding it in Settings > API Keys and inspecting network traffic anyway.

The Settings UI's description for this key tells the operator to restrict it by HTTP referrer
rather than relying on it staying secret, since the key is visible in the rendered page's DOM
once the panorama loads.
