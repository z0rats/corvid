// Mirrors backend/app/features/telegram_search/config/telegram_search_config.py's
// MAX_POSTS_DEFAULT/CAP.
export const MAX_POSTS_DEFAULT = 100;
export const MAX_POSTS_CAP = 500;

// The t.me/s preview serves ~20 posts per page.
const POSTS_PER_PAGE = 20;

export function estimateRequests(maxPosts) {
  // Profile card + preview pages + the "channel created" lookup.
  return 2 + Math.ceil(maxPosts / POSTS_PER_PAGE);
}

const HASH_TYPES = new Set(['md5', 'sha1', 'sha256']);

/** Where an extracted indicator of `type` (backend `indicators` key) is sent on click. */
export function indicatorPivotPath(type) {
  if (type === 'domains') return '/ioc-tools/domain-finder';
  if (HASH_TYPES.has(type)) return '/ioc-tools/bulk';
  return '/ioc-tools/lookup';
}

export const TELEGRAM_SCAN_PATH = '/telegram-search/new';
