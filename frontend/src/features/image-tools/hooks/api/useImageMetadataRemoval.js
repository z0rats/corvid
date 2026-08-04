import { useState } from 'react';
import { imageMetadataRemovalApi } from '../../services/api/imageMetadataRemovalApi';
import { imageUtils } from '../../utils/imageUtils';
import { createLogger } from '../../../../core/utils/logger';

const logger = createLogger('ImageMetadataRemoval');

// responseType 'blob' means a failed request's JSON error body also arrives
// as a Blob rather than parsed JSON - it has to be read back out as text.
async function extractErrorMessage(err) {
  const data = err.response?.data;
  if (data instanceof Blob && data.type.includes('json')) {
    try {
      const parsed = JSON.parse(await data.text());
      return parsed.detail || err.message;
    } catch {
      return err.message;
    }
  }
  return err.response?.data?.detail || err.message || 'Failed to remove metadata';
}

export function useImageMetadataRemoval() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const removeMetadata = async (file, mode) => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const { blob, filename } = await imageMetadataRemovalApi.removeMetadata(file, mode);
      imageUtils.downloadBlob(blob, filename);
      setSuccess(true);
    } catch (err) {
      logger.error('Error removing image metadata:', err);
      setError(await extractErrorMessage(err));
    }
    setLoading(false);
  };

  return { loading, error, success, removeMetadata };
}
