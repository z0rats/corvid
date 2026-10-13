// Pivot material for a finished run, computed by the backend (`pivot_service.build_pivots`,
// returned as `pivots` on a run) plus mail-address guesses made here. Everything is a hypothesis:
// shared handles are often different people, so results need manual verification.

export interface PivotUsername {
  value: string;
  /** reported: the profile page named it; link: a URL the owner typed in, resolved to an account. */
  kind: 'reported' | 'link';
  /** 'username' for a plain handle, else the platform ID type (vk_id, steam_id, ...). */
  id_type: string;
  /** False for platform IDs: a username search for a numeric ID wastes a whole scan. */
  searchable: boolean;
  /** Site a link-derived handle lives on. */
  site?: string | null;
  sites: string[];
}

export interface PivotItem {
  value: string;
  sites: string[];
}

export interface RunPivots {
  usernames: PivotUsername[];
  names: PivotItem[];
  emails: PivotItem[];
}

export const EMPTY_PIVOTS: RunPivots = { usernames: [], names: [], emails: [] };

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
