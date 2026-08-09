import { useEffect } from 'react';
import { Navigate, useLocation, useSearchParams } from 'react-router';
import { PREFILL_QUERY_PARAM } from '../utils/crossFeatureNav';

/**
 * Reads a value chained in from another feature (see crossFeatureNav.buildPrefillUrl), strips it
 * from the URL once consumed so it doesn't re-trigger on subsequent in-feature navigation, and -
 * when `onValue` is given - runs it exactly once for the incoming value (every call site used to
 * hand-roll this as its own `useEffect(() => { if (!prefillValue) return; ...; clearPrefill(); },
 * [prefillValue])`). Always returns the raw value too, since most callers also feed it to a form
 * field's initial value regardless of whether they also act on it via `onValue`.
 */
export function usePrefillFromQuery(onValue) {
  const [searchParams, setSearchParams] = useSearchParams();
  const prefillValue = searchParams.get(PREFILL_QUERY_PARAM);

  const clearPrefill = () => {
    const next = new URLSearchParams(searchParams);
    next.delete(PREFILL_QUERY_PARAM);
    setSearchParams(next, { replace: true });
  };

  useEffect(() => {
    if (!prefillValue || !onValue) return;
    onValue(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return prefillValue;
}

/**
 * Preserves a pivot's `?q=` when redirecting a feature's index route to its "new" tab - a bare
 * `to="new"` drops the search string, silently breaking `usePrefillFromQuery` downstream. Every
 * identity-style feature's root route (username/email/reddit-search, git-recon) uses this instead
 * of hand-rolling `useLocation()` + `<Navigate>` itself.
 */
export function IdentityRedirect({ to }) {
  const location = useLocation();
  return <Navigate to={{ pathname: to, search: location.search }} replace />;
}
