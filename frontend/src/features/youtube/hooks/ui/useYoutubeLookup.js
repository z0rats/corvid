import { useState, useCallback } from 'react';
import { useAtom } from 'jotai';
import { youtubeApi } from '../../services/api/youtubeApi';
import { youtubeLookupStateAtom } from '../../state/youtubeAtoms';
import { usePrefillFromQuery } from '../../../../core/hooks/usePrefillFromQuery';

export function useYoutubeLookup() {
  const [url, setUrl] = useState('');
  const [{ result, loading, error }, setLookupState] = useAtom(youtubeLookupStateAtom);

  const lookupVideo = useCallback(async (urlOverride) => {
    const urlValue = (urlOverride ?? url).trim();
    if (!urlValue) return;

    setLookupState({ result: null, loading: true, error: null });
    try {
      const data = await youtubeApi.lookup(urlValue);
      setLookupState({ result: data, loading: false, error: null });
    } catch (err) {
      setLookupState({
        result: null,
        loading: false,
        error: err.response?.data?.detail || err.message || 'YouTube lookup failed',
      });
    }
  }, [url, setLookupState]);

  usePrefillFromQuery(useCallback((value) => {
    setUrl(value);
    lookupVideo(value);
  }, [lookupVideo]));

  return { url, setUrl, result, loading, error, lookupVideo };
}
