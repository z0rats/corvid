import { useState, useCallback, useEffect } from 'react';
import { useAtom } from 'jotai';
import { youtubeApi } from '../../services/api/youtubeApi';
import { youtubeLookupStateAtom } from '../../state/youtubeAtoms';
import { usePrefillFromQuery } from '../../../../core/hooks/usePrefillFromQuery';

export function useYoutubeLookup() {
  const [url, setUrl] = useState('');
  const [{ result, loading, error }, setLookupState] = useAtom(youtubeLookupStateAtom);
  const { prefillValue, clearPrefill } = usePrefillFromQuery();

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

  useEffect(() => {
    if (!prefillValue) return;
    setUrl(prefillValue);
    lookupVideo(prefillValue);
    clearPrefill();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillValue]);

  return { url, setUrl, result, loading, error, lookupVideo };
}
