import { useState, useCallback, useEffect } from 'react';
import { useAtom } from 'jotai';
import { youtubeApi } from '../../services/api/youtubeApi';
import { youtubeLookupStateAtom } from '../../state/youtubeAtoms';
import { useUrlDrivenLookup } from '../../../../core/hooks/useUrlQuery';

export function useYoutubeLookup() {
  const [{ result, loading, error, lastQuery }, setLookupState] = useAtom(youtubeLookupStateAtom);

  const lookup = useCallback(async (urlValue) => {
    setLookupState({ lastQuery: urlValue, result: null, loading: true, error: null });
    try {
      const data = await youtubeApi.lookup(urlValue);
      setLookupState({ lastQuery: urlValue, result: data, loading: false, error: null });
    } catch (err) {
      setLookupState({
        lastQuery: urlValue,
        result: null,
        loading: false,
        error: err.response?.data?.detail || err.message || 'YouTube lookup failed',
      });
    }
  }, [setLookupState]);

  // The video URL lives in the page URL (?q=): pivots, reloads, bookmarks and Back/Forward all run through it.
  const { urlValue, submit } = useUrlDrivenLookup({ run: lookup, shownValue: lastQuery });
  const [url, setUrl] = useState(urlValue || lastQuery);
  useEffect(() => { if (urlValue) setUrl(urlValue); }, [urlValue]);

  const lookupVideo = useCallback((urlOverride) => submit(urlOverride ?? url), [submit, url]);

  return { url, setUrl, result, loading, error, lookupVideo };
}
