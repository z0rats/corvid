export const CONFIDENCE_ORDER = ['confirmed', 'likely', 'candidate', 'conflicting'] as const;

interface RatedSite {
  extra?: { confidence?: string } | null;
}

const rank = (site: RatedSite): number => {
  const index = CONFIDENCE_ORDER.indexOf(site.extra?.confidence as (typeof CONFIDENCE_ORDER)[number]);
  return index === -1 ? CONFIDENCE_ORDER.length : index;
};

/** Best-rated first; sites without a rating (a plain scan) keep their order, after rated ones.
 *  Stable, so equal ratings stay in the backend's alphabetical order. */
export function sortByConfidence<T extends RatedSite>(sites: T[]): T[] {
  return [...sites].sort((a, b) => rank(a) - rank(b));
}
