import { useCallback, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router';
import { PREFILL_QUERY_PARAM } from '../utils/crossFeatureNav';

/**
 * The current lookup value kept in the URL's `?q=` (the same param cross-feature pivots use), for
 * ephemeral one-shot lookups whose result should survive a reload, be bookmarkable, and move with
 * Back/Forward. Unlike usePrefillFromQuery - which consumes `?q=` once and strips it - the value
 * stays in the URL as long as it's the active lookup. Setting a new value pushes a history entry
 * unless `{ replace: true }` is passed.
 */
export function useUrlQuery() {
  const [searchParams, setSearchParams] = useSearchParams();
  const value = searchParams.get(PREFILL_QUERY_PARAM) ?? '';

  const setValue = useCallback((next, { replace = false } = {}) => {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      if (next) params.set(PREFILL_QUERY_PARAM, next);
      else params.delete(PREFILL_QUERY_PARAM);
      return params;
    }, { replace });
  }, [setSearchParams]);

  return [value, setValue];
}

/**
 * URL-driven runner for a cheap one-shot lookup: whenever `?q=` changes to a runnable value that
 * isn't the one already on screen (`shownValue`), `run(value)` fires - covering pivots, reloads,
 * bookmarks and Back/Forward alike. `submit(value)` is the form's entry point: a new value goes
 * into the URL (which then runs it), the value already in the URL re-runs directly. Returning to
 * the page with no `?q=` while a result is still shown puts that value back into the URL.
 */
export function useUrlDrivenLookup({ run, shownValue, isRunnable = (value) => Boolean(value) }) {
  const [urlValue, setUrlValue] = useUrlQuery();
  const runRef = useRef(run);
  runRef.current = run;
  const shownRef = useRef(shownValue);
  shownRef.current = shownValue;
  const isRunnableRef = useRef(isRunnable);
  isRunnableRef.current = isRunnable;

  useEffect(() => {
    const value = urlValue.trim();
    if (!value) {
      if (shownRef.current) setUrlValue(shownRef.current, { replace: true });
      return;
    }
    if (isRunnableRef.current(value) && value !== shownRef.current) runRef.current(value);
  }, [urlValue, setUrlValue]);

  const submit = useCallback((rawValue) => {
    const value = rawValue.trim();
    if (!isRunnableRef.current(value)) return;
    if (value === urlValue.trim()) runRef.current(value);
    else setUrlValue(value);
  }, [urlValue, setUrlValue]);

  return { urlValue, submit };
}
