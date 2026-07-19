import { useEffect, useState } from 'react';
import { iocLookupApi } from '../../../../shared/services/api/iocLookupApi';
import { createLogger } from '../../../../../../core/utils/logger';

const logger = createLogger('NewsfeedMentions');

export function useNewsfeedMentions(ioc) {
  const [mentions, setMentions] = useState([]);

  useEffect(() => {
    if (!ioc) {
      setMentions([]);
      return;
    }

    const abortController = new AbortController();

    iocLookupApi.fetchNewsfeedMentions(ioc, { signal: abortController.signal })
      .then((data) => setMentions(data?.mentions || []))
      .catch((error) => {
        if (error.name === 'AbortError' || error.name === 'CanceledError') return;
        logger.error('Failed to fetch newsfeed mentions:', error);
        setMentions([]);
      });

    return () => abortController.abort();
  }, [ioc]);

  return mentions;
}
