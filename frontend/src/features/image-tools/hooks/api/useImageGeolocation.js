import { useState } from 'react';
import { useAtomValue } from 'jotai';
import { hasLlmKeyAtom } from '../../../../core/state/atoms';
import { imageGeolocationApi } from '../../services/api/imageGeolocationApi';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ImageGeolocation');

export function useImageGeolocation() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const hasLlmKey = useAtomValue(hasLlmKeyAtom);

  const geolocateImage = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const geolocationResult = await imageGeolocationApi.geolocateImage(file);
      setResult(geolocationResult);
    } catch (err) {
      logger.error('Error geolocating image:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to analyze image location');
    }
    setLoading(false);
  };

  return { result, loading, error, hasLlmKey, geolocateImage };
}
