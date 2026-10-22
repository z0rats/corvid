import { useEffect, useState } from 'react';
import { investigationsService } from '../../../core/services/api/investigationsService';
import { createLogger } from '../../../core/utils/logger';

const logger = createLogger('useFeatureLabels');

/** feature key -> display label, from the backend's RunSource registry. Empty until loaded (or
 * on failure), in which case callers fall back to the raw key. */
export function useFeatureLabels() {
  const [labels, setLabels] = useState({});

  useEffect(() => {
    let ignore = false;
    investigationsService
      .features()
      .then((features) => {
        if (!ignore) setLabels(Object.fromEntries(features.map((f) => [f.feature, f.label])));
      })
      .catch((err) => logger.warn('Failed to load investigation features:', err));
    return () => { ignore = true; };
  }, []);

  return labels;
}
