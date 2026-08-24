import { useEffect, useState } from 'react';
import { useAtomValue } from 'jotai';
import { hasGoogleMapsKeyAtom } from '../../../../core/state/atoms';
import { streetViewApi } from '../../services/api/streetViewApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('StreetView');

// Only fetches the raw key when apiKeysState already says one is configured -
// avoids a wasted request on the (default) unconfigured case.
export default function useStreetViewKey() {
  const hasGoogleMapsKey = useAtomValue(hasGoogleMapsKeyAtom);
  const [key, setKey] = useState(null);

  useEffect(() => {
    if (!hasGoogleMapsKey) {
      setKey(null);
      return undefined;
    }

    let cancelled = false;
    streetViewApi.getKey()
      .then((data) => {
        if (!cancelled) setKey(data.key);
      })
      .catch((err) => {
        logger.error('Error fetching Street View key:', err);
      });

    return () => {
      cancelled = true;
    };
  }, [hasGoogleMapsKey]);

  return key;
}
