import { useSearchParams } from 'react-router-dom';
import { PREFILL_QUERY_PARAM } from '../utils/crossFeatureNav';

/**
 * Reads a value chained in from another feature (see crossFeatureNav.buildPrefillUrl)
 * and provides a way to strip it from the URL once consumed, so it doesn't re-trigger
 * on subsequent in-feature navigation.
 */
export function usePrefillFromQuery() {
  const [searchParams, setSearchParams] = useSearchParams();
  const prefillValue = searchParams.get(PREFILL_QUERY_PARAM);

  const clearPrefill = () => {
    const next = new URLSearchParams(searchParams);
    next.delete(PREFILL_QUERY_PARAM);
    setSearchParams(next, { replace: true });
  };

  return { prefillValue, clearPrefill };
}
