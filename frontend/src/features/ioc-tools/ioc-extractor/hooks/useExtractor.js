import { useState, useCallback, useMemo } from 'react';
import { useAsyncOperation } from '../../shared/hooks/useAsyncOperation';
import { extractorApi } from '../../shared/services/api/extractorApi';
import { collectAllIOCs, copyIOCsToClipboard, exportIOCsToFile } from '../utils/iocExportUtils';
import { logger } from '../../shared/utils/logger';

export function useExtractor() {
  const [extractedData, setExtractedData] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { isLoading, error, executeAsync, clearError } = useAsyncOperation();

  const extractFromFile = useCallback(async (file) => {
    if (!file) throw new Error('No file provided');

    logger.info('Starting file extraction', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type
    });

    setUploadProgress(0);

    try {
      const data = await extractorApi.extractFromFile(file, setUploadProgress);

      logger.info('File extraction completed', {
        fileName: file.name,
        totalIOCs: data.statistics?.total_unique_iocs || 0
      });

      setExtractedData(data);
      setUploadProgress(0);
      return data;
    } catch (error) {
      setUploadProgress(0);
      logger.error('File extraction failed', { fileName: file.name, error: error.message });
      throw error;
    }
  }, []);

  const extractFromText = useCallback(async (text) => {
    const result = await executeAsync(
      () => extractorApi.extractFromText(text),
      'Text IOC Extraction'
    );
    setExtractedData(result);
    return result;
  }, [executeAsync]);

  const copyAllIOCs = useCallback(async () => {
    const allIOCs = collectAllIOCs(extractedData);
    return copyIOCsToClipboard(allIOCs);
  }, [extractedData]);

  const exportAllIOCs = useCallback(() => {
    const allIOCs = collectAllIOCs(extractedData);
    return exportIOCsToFile(allIOCs);
  }, [extractedData]);

  const reset = useCallback(() => {
    setExtractedData(null);
    setUploadProgress(0);
    clearError();
    logger.debug('Extractor state reset');
  }, [clearError]);

  const statistics = useMemo(() => extractedData?.statistics || null, [extractedData]);

  return {
    extractedData,
    uploadProgress,
    isLoading,
    error,
    hasResults: Boolean(extractedData),
    extractFromFile,
    extractFromText,
    copyAllIOCs,
    exportAllIOCs,
    statistics,
    reset,
    clearError
  };
}
