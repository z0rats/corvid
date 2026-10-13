const PREFILL_PARAM = 'q';

/**
 * Provenance a pivot can carry next to its value (username-search: the run it came from, the
 * site to check it on, a label). Read and cleared together with `q` by usePrefillFromQuery -
 * a param not listed here is silently dropped, like any other.
 */
export const PREFILL_CONTEXT_PARAMS = ['parent', 'site', 'src'] as const;
export type PrefillContext = Partial<Record<(typeof PREFILL_CONTEXT_PARAMS)[number], string | number | null>>;

/**
 * Builds a URL to another feature with a value pre-filled via the `q` query param,
 * so the target feature's own hook (see usePrefillFromQuery) can pick it up on mount.
 */
export const buildPrefillUrl = (
  path: string,
  value: string,
  context: PrefillContext = {},
): string => {
  const params = new URLSearchParams({ [PREFILL_PARAM]: value });
  for (const key of PREFILL_CONTEXT_PARAMS) {
    const entry = context[key];
    if (entry !== undefined && entry !== null && entry !== '') params.set(key, String(entry));
  }
  return `${path}?${params.toString()}`;
};

export const PREFILL_QUERY_PARAM = PREFILL_PARAM;
