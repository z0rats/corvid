import { useState, useCallback } from 'react';
import { useAtom } from 'jotai';
import { instagramSearchApi } from '../../services/api/instagramSearchApi';
import { instagramSearchStateAtom } from '../../state/instagramSearchAtoms';
import { usePrefillFromQuery } from '../../../../core/hooks/usePrefillFromQuery';

export function useInstagramSearch() {
  const [username, setUsername] = useState('');
  const [{ result, loading, error }, setSearchState] = useAtom(instagramSearchStateAtom);

  const lookupProfile = useCallback(async (usernameOverride) => {
    const usernameValue = (usernameOverride ?? username).trim();
    if (!usernameValue) return;

    setSearchState({ result: null, loading: true, error: null });
    try {
      const data = await instagramSearchApi.lookupProfile(usernameValue);
      setSearchState({ result: data, loading: false, error: null });
    } catch (err) {
      setSearchState({
        result: null,
        loading: false,
        error: err.response?.data?.detail || err.message || 'Instagram profile lookup failed',
      });
    }
  }, [username, setSearchState]);

  usePrefillFromQuery(useCallback((value) => {
    setUsername(value);
    lookupProfile(value);
  }, [lookupProfile]));

  return { username, setUsername, result, loading, error, lookupProfile };
}
