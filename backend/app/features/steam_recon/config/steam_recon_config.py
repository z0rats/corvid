"""Static config for the Steam Recon feature."""

STEAM_API_BASE_URL = "https://api.steampowered.com"
STEAM_API_TIMEOUT = 15.0

# GetPlayerSummaries / GetPlayerBans accept at most this many SteamIDs per call.
PLAYER_BATCH_SIZE = 100

# `communityvisibilitystate` value meaning a fully public profile.
VISIBILITY_PUBLIC = 3

# Deep-links to third-party lookups, built from the SteamID64 with no network call. SteamDB and
# csstats.gg sit behind a Cloudflare bot challenge, so a scripted request gets a 403 - they
# still open fine in a browser, which is all a link needs.
QUICK_LINKS: tuple[tuple[str, str, str], ...] = (
    ("steam_profile", "Steam profile", "https://steamcommunity.com/profiles/{id}"),
    ("steamid_io", "steamid.io", "https://steamid.io/lookup/{id}"),
    ("steamdb", "SteamDB", "https://steamdb.info/calculator/{id}/"),
    ("csstats", "csstats.gg", "https://csstats.gg/player/{id}"),
    ("leetify", "Leetify", "https://leetify.com/app/profile/{id}"),
)


def build_quick_links(steamid64: str) -> list[dict[str, str]]:
    return [
        {"id": link_id, "label": label, "url": template.format(id=steamid64)}
        for link_id, label, template in QUICK_LINKS
    ]


# --- Scan (friends graph / close friends / geolocation) ---------------------------------

MAX_FRIENDS_DEFAULT = 200
MAX_FRIENDS_CAP = 500

# How many of the target's public friends have their own friend list fetched, to compute
# mutual-connection weight - the expensive step (one Steam Web API call each). Candidates
# beyond `max_friends` are dropped before this step, oldest `friend_since` first (see
# graph_service.select_candidates), on the assumption an older connection is more likely
# a genuinely close one than a friend added yesterday.
FRIEND_FETCH_CONCURRENCY = 8

# A friend-list fetch that hits Steam's rate limit is retried with backoff rather than
# immediately counted as failed - a scan of a few hundred friends is expected to brush the
# limit occasionally.
FRIEND_FETCH_MAX_RETRIES = 3
FRIEND_FETCH_RETRY_BACKOFF_SECONDS = 2.0

CLOSE_FRIENDS_TOP_N = 20

# Geolocation-by-social-graph confidence thresholds. `leader_share` = the winning country's
# share of total location-weighted votes; `min_voters`/`min_coverage` gate against a
# confident-looking result built from too little data.
GEO_HIGH_CONFIDENCE_SHARE = 0.5
GEO_HIGH_CONFIDENCE_MIN_VOTERS = 5
GEO_MEDIUM_CONFIDENCE_SHARE = 0.3
GEO_MEDIUM_CONFIDENCE_MIN_VOTERS = 3
GEO_MIN_COVERAGE_FOR_MEDIUM = 0.2

# Only the top few candidates per level are surfaced (the rest are noise once ranked).
GEO_TOP_CANDIDATES_PER_LEVEL = 3
