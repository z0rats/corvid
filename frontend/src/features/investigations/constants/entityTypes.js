// Entity types the backend graph returns (app/core/entities/model.py ENTITY_TYPES) with a colour
// each and the features a node of that type can pivot into via `?q=`. A type the backend adds
// later still renders, in FALLBACK_COLOR, with no pivots.

const IOC_LOOKUP = { key: 'iocLookup', path: '/ioc-tools/lookup' };
const USERNAME_SEARCH = { key: 'usernameSearch', path: '/username-search/new' };
const EMAIL_SEARCH = { key: 'emailSearch', path: '/email-search/new' };
const REDDIT_SEARCH = { key: 'redditSearch', path: '/reddit-search/new' };

export const ENTITY_TYPES = {
  ip: { color: '#1e88e5', pivots: [IOC_LOOKUP] },
  domain: { color: '#00897b', pivots: [IOC_LOOKUP] },
  url: { color: '#5e35b1', pivots: [IOC_LOOKUP] },
  email: { color: '#e53935', pivots: [IOC_LOOKUP, EMAIL_SEARCH] },
  hash: { color: '#6d4c41', pivots: [IOC_LOOKUP] },
  cve: { color: '#d81b60', pivots: [IOC_LOOKUP] },
  wallet: { color: '#f9a825', pivots: [IOC_LOOKUP] },
  username: { color: '#fb8c00', pivots: [USERNAME_SEARCH, EMAIL_SEARCH, REDDIT_SEARCH] },
  account: { color: '#43a047', pivots: [] },
  breach: { color: '#8e24aa', pivots: [] },
  asn: { color: '#3949ab', pivots: [] },
  netblock: { color: '#546e7a', pivots: [] },
  subreddit: { color: '#ff7043', pivots: [] },
};

export const FALLBACK_COLOR = '#9e9e9e';

export const entityColor = (type) => ENTITY_TYPES[type]?.color ?? FALLBACK_COLOR;

export const entityPivots = (type) => ENTITY_TYPES[type]?.pivots ?? [];
