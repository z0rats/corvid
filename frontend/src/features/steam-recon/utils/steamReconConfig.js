// Mirrors backend/app/features/steam_recon/config/steam_recon_config.py's MAX_FRIENDS_DEFAULT/CAP.
export const MAX_FRIENDS_DEFAULT = 200;
export const MAX_FRIENDS_CAP = 500;

// Rough Steam Web API call-count estimate shown next to the friends slider: one summaries batch,
// one bans batch, plus one GetFriendList call per candidate friend (the expensive step), plus a
// handful more when the CS2 report is requested (level/games/stats/comments).
const BASE_CALLS = 4;
const CS_REPORT_EXTRA_CALLS = 3;

export function estimateApiCalls(maxFriends, includeCsReport) {
  return maxFriends + BASE_CALLS + (includeCsReport ? CS_REPORT_EXTRA_CALLS : 0);
}
