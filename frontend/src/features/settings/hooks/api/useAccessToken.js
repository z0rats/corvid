import { useCallback, useState } from 'react';
import { settingsApi } from '../../services/api/settingsApi';
import { setAccessToken } from '../../../../core/utils/accessToken';

function errorMessage(err, fallback) {
  return err.response?.data?.detail || err.message || fallback;
}

/**
 * Regenerates the shared API access token. On success, immediately writes the
 * new token to localStorage (setAccessToken) so this browser tab keeps working
 * without a reload - every other tab/device/the browser extension still holds
 * the old, now-invalid token and needs it re-entered manually.
 */
export function useAccessToken() {
  const [regenerating, setRegenerating] = useState(false);

  const regenerate = useCallback(async (fallbackMessage) => {
    setRegenerating(true);
    try {
      const { access_token: newToken } = await settingsApi.regenerateAccessToken();
      setAccessToken(newToken);
      return { success: true, newToken };
    } catch (err) {
      return {
        success: false,
        message: errorMessage(err, fallbackMessage),
        errorCode: err.response?.data?.error_code,
      };
    } finally {
      setRegenerating(false);
    }
  }, []);

  return { regenerating, regenerate };
}
