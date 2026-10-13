// A site check is a Maigret run on a few named sites (confirming one pivot). Maigret's verdict
// per site is claimed / available / unknown (check failed or blocked) / illegal (handle not
// valid there); only the first two say anything about the account.
const INCONCLUSIVE = new Set(['unknown', 'illegal']);

/** Sites whose check ended without an answer, in the order given. */
export function inconclusiveSites(statuses: Record<string, string> | null | undefined): string[] {
  return Object.entries(statuses ?? {})
    .filter(([, status]) => INCONCLUSIVE.has(status))
    .map(([site]) => site);
}
