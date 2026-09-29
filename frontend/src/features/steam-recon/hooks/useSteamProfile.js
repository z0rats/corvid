import { useState, useCallback } from 'react';
import { useAtom } from 'jotai';
import { steamReconApi } from '../services/api/steamReconApi';
import { steamProfileStateAtom } from '../state/steamReconAtoms';
import { usePrefillFromQuery } from '../../../core/hooks/usePrefillFromQuery';

export function useSteamProfile() {
  const [target, setTarget] = useState('');
  const [{ result, loading, error, errorCode }, setState] = useAtom(steamProfileStateAtom);

  const lookupProfile = useCallback(async (targetOverride) => {
    const value = (targetOverride ?? target).trim();
    if (!value) return;

    setState({ result: null, loading: true, error: null, errorCode: null });
    try {
      const data = await steamReconApi.profile(value);
      setState({ result: data, loading: false, error: null, errorCode: null });
    } catch (err) {
      setState({
        result: null,
        loading: false,
        error: err.response?.data?.detail || err.message || 'Steam lookup failed',
        errorCode: err.response?.data?.error_code || null,
      });
    }
  }, [target, setState]);

  usePrefillFromQuery(useCallback((value) => {
    setTarget(value);
    lookupProfile(value);
  }, [lookupProfile]));

  return { target, setTarget, result, loading, error, errorCode, lookupProfile };
}
