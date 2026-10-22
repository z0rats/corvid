// Backend feature/run-source name -> that feature's history route. Shared by everything that
// links to a past run by (feature, id): alert deep-links and the start screen's activity feed.
// username_search's table is written by several sources, each reported under its own name.
const HISTORY_PATHS = {
  username_search: '/username-search/history',
  social_analyzer: '/username-search/history',
  threat_actor_usernames: '/username-search/history',
  email_search: '/email-search/history',
  git_recon: '/git-recon/history',
  amass: '/amass/history',
  ru_business_check: '/ru-business-check/history',
  steam_recon: '/steam-recon/history',
  instagram_search: '/instagram-search/history',
  telegram_search: '/telegram-search/history',
  phone_search: '/phone-search/history',
  reddit_search: '/reddit-search/history',
  ioc_lookup: '/ioc-tools/lookup/history',
};

/** History list route for a feature, or undefined if it has none. */
export const getHistoryPath = (feature) => HISTORY_PATHS[feature];

/** A single run's detail route, falling back to the list without an id. */
export function getRunPath(feature, id) {
  const base = HISTORY_PATHS[feature];
  if (!base) return undefined;
  return id == null ? base : `${base}/${id}`;
}
