import { useEffect, useState } from 'react';
import { usernameSearchApi } from '../../services/api/usernameSearchApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('HudsonRockCheck');

export function useHudsonRockCheck(username) {
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!username) {
      setResult(null);
      return;
    }

    const abortController = new AbortController();

    usernameSearchApi.checkHudsonRock(username, { signal: abortController.signal })
      .then(setResult)
      .catch((error) => {
        if (error.name === 'AbortError' || error.name === 'CanceledError') return;
        logger.error('Failed to check Hudson Rock:', error);
        setResult(null);
      });

    return () => abortController.abort();
  }, [username]);

  return result;
}
