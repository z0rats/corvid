// Pivot material harvested from found profiles (see backend `_build_discovered_extra`) plus
// mail-address guesses. Everything here is a hypothesis: shared handles are often different
// people, so results need manual verification.

export interface FoundSiteExtra {
  discovered_usernames?: Array<{ value: string; type: string }>;
  discovered_names?: string[];
  discovered_links?: string[];
}

export interface FoundSite {
  site_name: string;
  extra?: FoundSiteExtra | null;
}

export interface DiscoveredItem {
  value: string;
  sites: string[];
}

export interface DiscoveredUsername extends DiscoveredItem {
  type: string;
}

export interface DiscoveredIdentifiers {
  usernames: DiscoveredUsername[];
  names: DiscoveredItem[];
}

/** Dedupes (case-insensitively) across sites, excluding the handle that was searched. */
export function aggregateDiscovered(
  sites: FoundSite[] | null | undefined,
  searchedUsername: string,
): DiscoveredIdentifiers {
  const self = searchedUsername.trim().toLowerCase();
  const usernames = new Map<string, DiscoveredUsername>();
  const names = new Map<string, DiscoveredItem>();

  const add = <T extends DiscoveredItem>(map: Map<string, T>, value: string, site: string, make: () => T) => {
    const key = value.trim().toLowerCase();
    if (!key) return;
    const entry = map.get(key) ?? make();
    if (!entry.sites.includes(site)) entry.sites.push(site);
    map.set(key, entry);
  };

  (sites ?? []).forEach(({ site_name: site, extra }) => {
    extra?.discovered_usernames?.forEach(({ value, type }) => {
      if (value.trim().toLowerCase() === self) return;
      add(usernames, value, site, () => ({ value: value.trim(), type, sites: [] }));
    });
    extra?.discovered_names?.forEach((name) => add(names, name, site, () => ({ value: name.trim(), sites: [] })));
  });

  return { usernames: [...usernames.values()], names: [...names.values()] };
}

// Consumer providers first; mail.ru/yandex.ru because a lot of the audience this tool serves
// (and the ru-market checks elsewhere in it) lives there.
export const EMAIL_GUESS_DOMAINS = [
  'gmail.com', 'outlook.com', 'yahoo.com', 'proton.me', 'icloud.com', 'mail.ru', 'yandex.ru',
];

const LOCAL_PART = /^[a-z0-9][a-z0-9._-]{0,62}$/i;

/** `username@provider` candidates; empty when the handle can't be a valid local part. */
export function guessEmails(username: string, domains: string[] = EMAIL_GUESS_DOMAINS): string[] {
  const local = username.trim().toLowerCase();
  if (!LOCAL_PART.test(local) || local.endsWith('.') || local.includes('..')) return [];
  return domains.map((domain) => `${local}@${domain}`);
}
