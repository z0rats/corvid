// Likely usernames behind an email address: people often register the same handle as their
// mailbox name. Pure and offline. Only rules that hold for the address itself are applied
// (sub-addressing `+tag`, Gmail ignoring dots); everything else is a guess about habits, same as
// usernameVariants.ts. Provider-specific tables (Yahoo `-` etc.) are deliberately left out.

export type EmailCandidateReason = 'exact' | 'untagged' | 'gmailDots' | 'separator';

export interface EmailUsernameCandidate {
  value: string;
  reason: EmailCandidateReason;
}

export const MIN_CANDIDATE_LENGTH = 3;

const EMAIL_RE = /^([^\s@]+)@([^\s@]+\.[^\s@]+)$/;
const VALID_CANDIDATE = /^[a-z0-9._-]+$/;
const GMAIL_DOMAINS = new Set(['gmail.com', 'googlemail.com']);
const SEPARATOR_JOINERS = ['_', '', '-', '.'];

/** Splits a bare email address into local part and domain, or null if it isn't one. */
export function parseEmail(input: string): { local: string; domain: string } | null {
  const match = EMAIL_RE.exec(input.trim());
  if (!match) return null;
  return { local: match[1], domain: match[2].toLowerCase() };
}

/**
 * Ordered candidates for `email`: the local part as-is, without its `+tag`, the Gmail dotless
 * form, then `first.last` separator variants. Deduplicated, lowercase, at least
 * MIN_CANDIDATE_LENGTH characters, never containing `+` (not a valid username anywhere).
 * Returns [] for anything that isn't an email.
 */
export function emailUsernameCandidates(email: string): EmailUsernameCandidate[] {
  const parsed = parseEmail(email);
  if (!parsed) return [];
  const exact = parsed.local.toLowerCase();
  const untagged = exact.split('+')[0];
  const tokens = untagged.split(/[._-]+/).filter(Boolean);

  const ordered: Array<[EmailCandidateReason, string]> = [
    ['exact', exact],
    ['untagged', untagged],
  ];
  if (GMAIL_DOMAINS.has(parsed.domain)) ordered.push(['gmailDots', untagged.replace(/\./g, '')]);
  if (tokens.length >= 2) {
    SEPARATOR_JOINERS.forEach((joiner) => ordered.push(['separator', tokens.join(joiner)]));
  }

  const seen = new Set<string>();
  const out: EmailUsernameCandidate[] = [];
  for (const [reason, value] of ordered) {
    if (seen.has(value) || value.length < MIN_CANDIDATE_LENGTH || !VALID_CANDIDATE.test(value)) continue;
    seen.add(value);
    out.push({ value, reason });
  }
  return out;
}
