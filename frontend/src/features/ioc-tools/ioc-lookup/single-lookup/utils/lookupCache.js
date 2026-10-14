// Per-service single-lookup responses for this browser session, so revisiting a lookup (Back from
// another tool, re-opening ?q=...) doesn't re-spend provider quota - several providers' free tiers
// allow only a handful of requests per minute. Errors are never cached, so a rate-limited or
// failed provider is retried on the next visit. An explicit re-search bypasses it.
export const LOOKUP_CACHE_TTL_MS = 15 * 60 * 1000;

const cache = new Map();
const cacheKey = (serviceKey, iocType, ioc) => `${serviceKey}\u0000${iocType}\u0000${ioc}`;

export function getCachedLookup(serviceKey, iocType, ioc) {
  const key = cacheKey(serviceKey, iocType, ioc);
  const entry = cache.get(key);
  if (!entry) return undefined;
  if (Date.now() - entry.at > LOOKUP_CACHE_TTL_MS) {
    cache.delete(key);
    return undefined;
  }
  return entry.data;
}

export function setCachedLookup(serviceKey, iocType, ioc, data) {
  cache.set(cacheKey(serviceKey, iocType, ioc), { data, at: Date.now() });
}

export function clearLookupCache() {
  cache.clear();
}
