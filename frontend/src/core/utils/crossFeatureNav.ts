const PREFILL_PARAM = 'q';

/**
 * Builds a URL to another feature with a value pre-filled via the `q` query param,
 * so the target feature's own hook (see usePrefillFromQuery) can pick it up on mount.
 */
export const buildPrefillUrl = (path, value) => `${path}?${PREFILL_PARAM}=${encodeURIComponent(value)}`;

export const PREFILL_QUERY_PARAM = PREFILL_PARAM;
